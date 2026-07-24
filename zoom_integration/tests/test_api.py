from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from zoom_integration import api
from zoom_integration.tests.zoom_fixtures import (
	ADD_MEETING_REGISTRANT_RESPONSE,
	CREATE_MEETING_RESPONSE,
	MEETING_PARTICIPANTS_RESPONSE,
	MEETING_REGISTRANTS_LIST_RESPONSE,
	NOT_FOUND_DELETE_RESPONSE,
	mock_response,
)

HEADERS = {"Authorization": "Bearer test-token", "content-type": "application/json"}


class TestZoomAPI(IntegrationTestCase):
	def test_create_meeting_posts_to_meetings_endpoint_and_returns_data(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.post.return_value = mock_response(201, CREATE_MEETING_RESPONSE)

			result = api.create_zoom_session("meetings", {"topic": "Test Meeting", "type": 2})

			called_url = mock_requests.post.call_args.args[0]
			self.assertTrue(called_url.endswith("/users/me/meetings"))
			self.assertEqual(result["id"], 91234567890)
			self.assertEqual(result["uuid"], "aDEFghiJKLmno12PQ==")
			self.assertEqual(result["join_url"], CREATE_MEETING_RESPONSE["join_url"])

	def test_update_meeting_patches_meeting_endpoint(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.patch.return_value = mock_response(204)

			api.update_zoom_session("meetings", "91234567890", {"topic": "New"})

			called_url = mock_requests.patch.call_args.args[0]
			self.assertTrue(called_url.endswith("/meetings/91234567890"))

	def test_delete_meeting_returns_true_on_204(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.delete.return_value = mock_response(204)
			self.assertTrue(api.delete_zoom_session("meetings", "91234567890"))

	def test_delete_meeting_returns_false_when_already_gone(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.delete.return_value = mock_response(404, NOT_FOUND_DELETE_RESPONSE)
			self.assertFalse(api.delete_zoom_session("meetings", "91234567890"))

	def test_add_registrant_returns_registrant_id_and_join_url(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.post.return_value = mock_response(201, ADD_MEETING_REGISTRANT_RESPONSE)

			result = api.add_zoom_registrant(
				"meetings", "91234567890", {"email": "alice@example.com", "first_name": "Alice"}
			)

			called_url = mock_requests.post.call_args.args[0]
			self.assertTrue(called_url.endswith("/meetings/91234567890/registrants"))
			self.assertEqual(result["registrant_id"], "abcDEF12ghIJ")
			self.assertEqual(result["join_url"], ADD_MEETING_REGISTRANT_RESPONSE["join_url"])

	def test_get_participants_uses_past_meetings_uuid_and_returns_list(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.get.return_value = mock_response(200, MEETING_PARTICIPANTS_RESPONSE)

			result = api.get_zoom_participants("meetings", "aDEFghiJKLmno12PQ==")

			called_url = mock_requests.get.call_args.args[0]
			self.assertIn("/past_meetings/", called_url)
			self.assertEqual(len(result), 2)
			self.assertEqual(result[0]["user_email"], "alice@example.com")

	def test_get_registrants_returns_list(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.get.return_value = mock_response(200, MEETING_REGISTRANTS_LIST_RESPONSE)

			result = api.get_zoom_registrants("meetings", "91234567890")

			called_url = mock_requests.get.call_args.args[0]
			self.assertIn("/meetings/91234567890/registrants", called_url)
			self.assertEqual(result[0]["email"], "alice@example.com")

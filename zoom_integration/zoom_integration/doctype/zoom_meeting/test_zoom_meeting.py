from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import (
	ADD_MEETING_REGISTRANT_RESPONSE,
	CREATE_MEETING_RESPONSE,
)

CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_meeting.zoom_meeting"


class TestZoomMeeting(IntegrationTestCase):
	def _new_meeting(self):
		return frappe.get_doc(
			{
				"doctype": "Zoom Meeting",
				"title": "Test Meeting",
				"date": "2026-08-01",
				"start_time": "10:00:00",
				"duration": 3600,
				"timezone": "Asia/Calcutta",
			}
		)

	def test_insert_creates_meeting_on_zoom_and_stores_ids(self):
		with patch(f"{CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE) as mock_create:
			meeting = self._new_meeting().insert()

			resource, body = mock_create.call_args.args
			self.assertEqual(resource, "meetings")
			self.assertEqual(body["type"], 2)
			self.assertEqual(body["settings"]["approval_type"], 0)
			self.assertEqual(meeting.zoom_meeting_id, "91234567890")
			self.assertEqual(meeting.zoom_meeting_uuid, "aDEFghiJKLmno12PQ==")
			self.assertEqual(meeting.zoom_link, CREATE_MEETING_RESPONSE["join_url"])

	def test_add_registrant_returns_registrant_id_and_join_url(self):
		with patch(f"{CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE):
			meeting = self._new_meeting().insert()

		with patch(
			f"{CONTROLLER}.add_zoom_registrant", return_value=ADD_MEETING_REGISTRANT_RESPONSE
		) as mock_add:
			result = meeting.add_registrant("alice@example.com", "Alice", "Smith")

			resource, session_id, body = mock_add.call_args.args
			self.assertEqual(resource, "meetings")
			self.assertEqual(session_id, "91234567890")
			self.assertEqual(body["email"], "alice@example.com")
			self.assertEqual(result["registrant_id"], "abcDEF12ghIJ")
			self.assertEqual(result["join_url"], ADD_MEETING_REGISTRANT_RESPONSE["join_url"])

	def test_sync_attendance_creates_records_from_participants(self):
		from zoom_integration.tests.zoom_fixtures import MEETING_PARTICIPANTS_RESPONSE

		with patch(f"{CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE):
			meeting = self._new_meeting().insert()

		participants = MEETING_PARTICIPANTS_RESPONSE["participants"]
		with patch(f"{CONTROLLER}.get_zoom_participants", return_value=participants):
			meeting.sync_attendance()

		records = frappe.get_all(
			"Zoom Webinar Attendance Record",
			filters={"meeting": meeting.name},
			fields=["user_email", "total_duration"],
		)
		emails = {r.user_email for r in records}
		self.assertEqual(emails, {"alice@example.com", "bob@example.com"})

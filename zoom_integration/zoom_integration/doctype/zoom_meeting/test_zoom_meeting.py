from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import (
	CREATE_MEETING_RESPONSE,
	MEETING_PARTICIPANTS_RESPONSE,
	add_meeting_registrant_response,
	create_meeting_response,
)

CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_meeting.zoom_meeting"


class TestZoomMeeting(IntegrationTestCase):
	def _insert_meeting(self):
		response = create_meeting_response()
		with patch(f"{CONTROLLER}.create_zoom_session", return_value=response) as mock_create:
			meeting = frappe.get_doc(
				{
					"doctype": "Zoom Meeting",
					"title": "Test Meeting",
					"date": "2026-08-01",
					"start_time": "10:00:00",
					"duration": 3600,
					"timezone": "Asia/Calcutta",
				}
			).insert()

		return meeting, response, mock_create

	def test_insert_creates_meeting_on_zoom_and_stores_ids(self):
		meeting, response, mock_create = self._insert_meeting()

		resource, body = mock_create.call_args.args
		self.assertEqual(resource, "meetings")
		self.assertEqual(body["type"], 2)
		self.assertEqual(body["settings"]["approval_type"], 0)
		self.assertEqual(meeting.zoom_meeting_id, str(response["id"]))
		self.assertEqual(meeting.zoom_meeting_uuid, CREATE_MEETING_RESPONSE["uuid"])
		self.assertEqual(meeting.zoom_link, CREATE_MEETING_RESPONSE["join_url"])

	def test_meeting_is_named_by_its_zoom_meeting_id(self):
		meeting, response, _ = self._insert_meeting()

		self.assertEqual(meeting.name, str(response["id"]))

	def test_add_registrant_returns_registrant_id_and_join_url(self):
		meeting, response, _ = self._insert_meeting()
		registrant = add_meeting_registrant_response()

		with patch(f"{CONTROLLER}.add_zoom_registrant", return_value=registrant) as mock_add:
			result = meeting.add_registrant("alice@example.com", "Alice", "Smith")

		resource, session_id, body = mock_add.call_args.args
		self.assertEqual(resource, "meetings")
		self.assertEqual(session_id, str(response["id"]))
		self.assertEqual(body["email"], "alice@example.com")
		self.assertEqual(result["registrant_id"], registrant["registrant_id"])
		self.assertEqual(result["join_url"], registrant["join_url"])

	def test_sync_attendance_creates_records_against_the_meeting(self):
		meeting, _, _ = self._insert_meeting()

		participants = MEETING_PARTICIPANTS_RESPONSE["participants"]
		with patch(f"{CONTROLLER}.get_zoom_participants", return_value=participants):
			meeting.sync_attendance()

		records = frappe.get_all(
			"Zoom Session Attendance Record",
			filters={"reference_doctype": "Zoom Meeting", "reference_name": meeting.name},
			fields=["user_email", "total_duration"],
		)
		self.assertEqual({r.user_email for r in records}, {"alice@example.com", "bob@example.com"})

	def test_sync_attendance_sums_duration_across_rejoins(self):
		meeting, _, _ = self._insert_meeting()

		participants = [
			{"user_email": "alice@example.com", "name": "Alice", "duration": 600},
			{"user_email": "alice@example.com", "name": "Alice", "duration": 900},
		]
		with patch(f"{CONTROLLER}.get_zoom_participants", return_value=participants):
			meeting.sync_attendance()

		total_duration = frappe.db.get_value(
			"Zoom Session Attendance Record",
			{"reference_name": meeting.name, "user_email": "alice@example.com"},
			"total_duration",
		)
		self.assertEqual(total_duration, 1500)

	def test_saving_without_changes_does_not_call_zoom(self):
		meeting, _, _ = self._insert_meeting()
		# reload: a freshly inserted doc still holds `date` as the string it was given,
		# so only a DB-loaded doc exercises the real comparison
		reloaded = frappe.get_doc("Zoom Meeting", meeting.name)

		with patch(f"{CONTROLLER}.update_zoom_session") as mock_update:
			reloaded.save()

		mock_update.assert_not_called()

	def test_saving_a_changed_date_calls_zoom(self):
		meeting, _, _ = self._insert_meeting()
		reloaded = frappe.get_doc("Zoom Meeting", meeting.name)

		with patch(f"{CONTROLLER}.update_zoom_session") as mock_update:
			reloaded.date = "2026-09-02"
			reloaded.save()

		mock_update.assert_called_once()

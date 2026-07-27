# Copyright (c) 2025, Build With Hussain and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import (
	WEBINAR_PARTICIPANTS,
	create_webinar_response,
	mock_response,
	mock_zoom_post,
	webinar_registrants,
)

CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_webinar.zoom_webinar"


class IntegrationTestZoomWebinar(IntegrationTestCase):
	def _insert_webinar(self, title="Test Webinar"):
		with mock_zoom_post(CONTROLLER, 201, create_webinar_response()):
			return frappe.get_doc(
				{
					"doctype": "Zoom Webinar",
					"title": title,
					"date": "2026-08-01",
					"start_time": "10:00:00",
					"duration": 3600,
					"timezone": "Asia/Calcutta",
				}
			).insert()

	def test_sync_registrations_creates_registrations_against_the_webinar(self):
		webinar = self._insert_webinar("Registrations Webinar")
		registrants = webinar_registrants()

		with patch(f"{CONTROLLER}.get_webinar_registrant_details", return_value=registrants):
			webinar.sync_registrations_from_zoom()

		registrations = frappe.get_all(
			"Zoom Session Registration",
			filters={"reference_doctype": "Zoom Webinar", "reference_name": webinar.name},
			fields=["email", "registrant_id"],
		)
		self.assertEqual([r.email for r in registrations], ["carol@example.com"])
		self.assertEqual(registrations[0].registrant_id, registrants[0]["id"])

	def test_sync_attendance_creates_records_against_the_webinar(self):
		webinar = self._insert_webinar("Attendance Webinar")

		with (
			patch(f"{CONTROLLER}.get_webinar_attendance_details", return_value=WEBINAR_PARTICIPANTS),
			patch(f"{CONTROLLER}.get_webinar_registrant_details", return_value=[]),
		):
			webinar.sync_attendance()

		records = frappe.get_all(
			"Zoom Session Attendance Record",
			filters={"reference_doctype": "Zoom Webinar", "reference_name": webinar.name},
			fields=["user_email", "total_duration"],
		)
		self.assertEqual({r.user_email for r in records}, {"carol@example.com", "dan@example.com"})

	def test_saving_without_changes_does_not_call_zoom(self):
		webinar = self._insert_webinar("Unchanged Webinar")
		reloaded = frappe.get_doc("Zoom Webinar", webinar.name)

		with mock_zoom_post(CONTROLLER, 204, {}) as mock_requests:
			mock_requests.patch.return_value = mock_response(204, {})
			reloaded.save()

		mock_requests.patch.assert_not_called()

	def test_attendance_does_not_borrow_another_sessions_registration(self):
		webinar = self._insert_webinar("Scoped Webinar")
		other = self._insert_webinar("Other Webinar")

		# same attendee, registered only on the other webinar
		frappe.get_doc(
			{
				"doctype": "Zoom Session Registration",
				"reference_doctype": "Zoom Webinar",
				"reference_name": other.name,
				"email": "carol@example.com",
				"first_name": "Carol",
				"registrant_id": frappe.generate_hash(length=12),
				"synced_from_zoom": 1,
			}
		).insert()

		with (
			patch(f"{CONTROLLER}.get_webinar_attendance_details", return_value=WEBINAR_PARTICIPANTS[:1]),
			patch(f"{CONTROLLER}.get_webinar_registrant_details", return_value=[]),
		):
			webinar.sync_attendance()

		linked = frappe.db.get_value(
			"Zoom Session Attendance Record",
			{"reference_name": webinar.name, "user_email": "carol@example.com"},
			"registration",
		)
		self.assertIsNone(linked)

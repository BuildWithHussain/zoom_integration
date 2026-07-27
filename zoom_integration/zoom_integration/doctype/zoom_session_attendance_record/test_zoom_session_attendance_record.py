# Copyright (c) 2025, Build With Hussain and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import create_meeting_response

MEETING_CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_meeting.zoom_meeting"


class IntegrationTestZoomSessionAttendanceRecord(IntegrationTestCase):
	def _insert_meeting(self):
		with patch(f"{MEETING_CONTROLLER}.create_zoom_session", return_value=create_meeting_response()):
			return frappe.get_doc(
				{
					"doctype": "Zoom Meeting",
					"title": "Attendance Meeting",
					"date": "2026-08-01",
					"start_time": "10:00:00",
					"duration": 3600,
					"timezone": "Asia/Calcutta",
				}
			).insert()

	def _new_record(self, reference_doctype, reference_name, **kwargs):
		return frappe.get_doc(
			{
				"doctype": "Zoom Session Attendance Record",
				"reference_doctype": reference_doctype,
				"reference_name": reference_name,
				"user_email": "alice@example.com",
				"full_name": "Alice Smith",
				"total_duration": 3200,
				**kwargs,
			}
		)

	def test_record_stores_the_session_it_belongs_to(self):
		meeting = self._insert_meeting()

		record = self._new_record("Zoom Meeting", meeting.name).insert()

		self.assertEqual(record.reference_doctype, "Zoom Meeting")
		self.assertEqual(record.reference_name, meeting.name)

	def test_reference_doctype_outside_zoom_sessions_is_rejected(self):
		record = self._new_record("User", "Administrator")

		self.assertRaises(frappe.ValidationError, record.insert)

	def test_reference_name_is_mandatory(self):
		record = frappe.get_doc(
			{
				"doctype": "Zoom Session Attendance Record",
				"reference_doctype": "Zoom Meeting",
				"user_email": "alice@example.com",
				"total_duration": 3200,
			}
		)

		self.assertRaises(frappe.MandatoryError, record.insert)

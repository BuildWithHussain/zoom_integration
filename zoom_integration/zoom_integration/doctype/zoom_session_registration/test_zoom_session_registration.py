# Copyright (c) 2025, Build With Hussain and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import ADD_MEETING_REGISTRANT_RESPONSE, CREATE_MEETING_RESPONSE

MEETING_CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_meeting.zoom_meeting"


class IntegrationTestZoomSessionRegistration(IntegrationTestCase):
	def test_registration_for_meeting_calls_meeting_add_registrant(self):
		with patch(f"{MEETING_CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE):
			meeting = frappe.get_doc(
				{
					"doctype": "Zoom Meeting",
					"title": "Reg Meeting",
					"date": "2026-08-01",
					"start_time": "10:00:00",
					"duration": 3600,
					"timezone": "Asia/Calcutta",
				}
			).insert()

		with patch(f"{MEETING_CONTROLLER}.add_zoom_registrant", return_value=ADD_MEETING_REGISTRANT_RESPONSE):
			registration = frappe.get_doc(
				{
					"doctype": "Zoom Session Registration",
					"meeting": meeting.name,
					"email": "alice@example.com",
					"first_name": "Alice",
					"last_name": "Smith",
				}
			).insert()
			registration.submit()

		self.assertEqual(registration.registrant_id, "abcDEF12ghIJ")
		self.assertEqual(registration.join_url, ADD_MEETING_REGISTRANT_RESPONSE["join_url"])

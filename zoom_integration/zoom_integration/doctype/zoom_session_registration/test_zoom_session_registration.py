# Copyright (c) 2025, Build With Hussain and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import (
	add_meeting_registrant_response,
	add_webinar_registrant_response,
	create_meeting_response,
	create_webinar_response,
	mock_response,
)

MEETING_CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_meeting.zoom_meeting"
WEBINAR_CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_webinar.zoom_webinar"


class IntegrationTestZoomSessionRegistration(IntegrationTestCase):
	def _insert_meeting(self):
		with patch(f"{MEETING_CONTROLLER}.create_zoom_session", return_value=create_meeting_response()):
			return frappe.get_doc(
				{
					"doctype": "Zoom Meeting",
					"title": "Reg Meeting",
					"date": "2026-08-01",
					"start_time": "10:00:00",
					"duration": 3600,
					"timezone": "Asia/Calcutta",
				}
			).insert()

	def _insert_webinar(self):
		with patch(f"{WEBINAR_CONTROLLER}.requests") as mock_requests:
			mock_requests.post.return_value = mock_response(201, create_webinar_response())
			return frappe.get_doc(
				{
					"doctype": "Zoom Webinar",
					"title": "Reg Webinar",
					"date": "2026-08-01",
					"start_time": "10:00:00",
					"duration": 3600,
					"timezone": "Asia/Calcutta",
				}
			).insert()

	def _new_registration(self, session, **kwargs):
		return frappe.get_doc(
			{
				"doctype": "Zoom Session Registration",
				"reference_doctype": session.doctype,
				"reference_name": session.name,
				"email": "alice@example.com",
				"first_name": "Alice",
				"last_name": "Smith",
				**kwargs,
			}
		)

	def test_registration_for_meeting_calls_meeting_add_registrant(self):
		meeting = self._insert_meeting()
		registration = self._new_registration(meeting).insert()
		registrant = add_meeting_registrant_response()

		with patch(f"{MEETING_CONTROLLER}.add_zoom_registrant", return_value=registrant) as mock_add:
			registration.submit()

		resource, session_id, _ = mock_add.call_args.args
		self.assertEqual(resource, "meetings")
		self.assertEqual(session_id, meeting.zoom_meeting_id)
		self.assertEqual(registration.registrant_id, registrant["registrant_id"])
		self.assertEqual(registration.join_url, registrant["join_url"])

	def test_registration_for_webinar_calls_webinar_add_registrant(self):
		webinar = self._insert_webinar()
		registration = self._new_registration(webinar, email="carol@example.com", first_name="Carol").insert()
		registrant = add_webinar_registrant_response()

		with patch(f"{WEBINAR_CONTROLLER}.requests") as mock_requests:
			mock_requests.post.return_value = mock_response(200, registrant)
			registration.submit()

		called_url = mock_requests.post.call_args.args[0]
		self.assertTrue(called_url.endswith(f"/webinars/{webinar.zoom_webinar_id}/registrants"))
		self.assertEqual(registration.registrant_id, registrant["registrant_id"])
		self.assertEqual(registration.join_url, registrant["join_url"])

	def test_additional_params_are_forwarded_to_zoom(self):
		meeting = self._insert_meeting()
		registration = self._new_registration(
			meeting,
			email="bob@example.com",
			additional_params=[{"key": "org", "value": "Frappe"}],
		).insert()

		with patch(
			f"{MEETING_CONTROLLER}.add_zoom_registrant", return_value=add_meeting_registrant_response()
		) as mock_add:
			registration.submit()

		body = mock_add.call_args.args[2]
		self.assertEqual(body["org"], "Frappe")

	def test_reference_doctype_outside_zoom_sessions_is_rejected(self):
		registration = self._new_registration(frappe.get_doc("User", "Administrator"))

		self.assertRaises(frappe.ValidationError, registration.insert)

	def test_reference_name_is_mandatory(self):
		registration = frappe.get_doc(
			{
				"doctype": "Zoom Session Registration",
				"reference_doctype": "Zoom Meeting",
				"email": "alice@example.com",
				"first_name": "Alice",
			}
		)

		self.assertRaises(frappe.MandatoryError, registration.insert)

import frappe
from frappe.tests import IntegrationTestCase


class TestRenameMeetingsToZoomID(IntegrationTestCase):
	def test_every_meeting_is_named_after_its_zoom_meeting_id(self):
		stale = frappe.get_all(
			"Zoom Meeting",
			fields=["name", "zoom_meeting_id"],
			filters={"zoom_meeting_id": ["is", "set"]},
		)
		mismatched = [row.name for row in stale if row.name != row.zoom_meeting_id]

		self.assertEqual(mismatched, [])

	def test_events_point_at_meetings_that_exist(self):
		linked = frappe.get_all("Buzz Event", filters={"zoom_meeting": ["is", "set"]}, pluck="zoom_meeting")
		missing = [name for name in linked if not frappe.db.exists("Zoom Meeting", name)]

		self.assertEqual(missing, [])

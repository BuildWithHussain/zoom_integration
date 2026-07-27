import frappe
from frappe.tests import IntegrationTestCase

OLD_DOCTYPES = (
	"Zoom Webinar Registration",
	"Zoom Webinar Attendance Record",
	"Zoom Webinar Additional Param",
)


class TestSessionRename(IntegrationTestCase):
	def test_additional_params_point_at_session_child_doctype(self):
		field = frappe.get_meta("Zoom Session Registration").get_field("additional_params")
		self.assertEqual(field.options, "Zoom Session Additional Param")

	def test_old_webinar_doctypes_are_gone(self):
		for doctype in OLD_DOCTYPES:
			self.assertFalse(frappe.db.exists("DocType", doctype), doctype)

	def test_stub_report_is_removed(self):
		self.assertFalse(frappe.db.exists("Report", "Consolidated Webinar Attendance"))

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.patches.backfill_session_reference import DOCTYPES, LEGACY_FIELDS, execute


class TestBackfillSessionReference(IntegrationTestCase):
	def test_every_row_carries_a_supported_reference_doctype(self):
		for doctype in DOCTYPES:
			stale = frappe.get_all(
				doctype,
				filters={"reference_doctype": ["not in", list(LEGACY_FIELDS.values())]},
				pluck="name",
				limit=5,
			)
			self.assertEqual(stale, [], f"{doctype} rows not on a Zoom session: {stale}")

	def test_rerunning_the_backfill_leaves_references_untouched(self):
		before = {
			doctype: frappe.get_all(
				doctype, fields=["name", "reference_doctype", "reference_name"], order_by="name"
			)
			for doctype in DOCTYPES
		}

		execute()

		for doctype in DOCTYPES:
			after = frappe.get_all(
				doctype, fields=["name", "reference_doctype", "reference_name"], order_by="name"
			)
			self.assertEqual(after, before[doctype], doctype)

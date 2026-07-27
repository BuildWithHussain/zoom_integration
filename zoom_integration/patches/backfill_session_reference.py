import frappe

DOCTYPES = ("Zoom Session Registration", "Zoom Session Attendance Record")
LEGACY_FIELDS = {"webinar": "Zoom Webinar", "meeting": "Zoom Meeting"}


def execute():
	"""Fold the separate `webinar` and `meeting` links into one dynamic reference.

	post_model_sync, so the new columns exist. Old ones stay for `bench trim-tables`,
	which is why this only fills empty references: the legacy columns are not kept in
	step afterwards, so overwriting a set reference would undo any later rename.
	"""
	for doctype in DOCTYPES:
		for legacy_field, reference_doctype in LEGACY_FIELDS.items():
			if not frappe.db.has_column(doctype, legacy_field):
				continue

			table = frappe.qb.DocType(doctype)
			legacy_column = getattr(table, legacy_field)
			frappe.qb.update(table).set(table.reference_doctype, reference_doctype).set(
				table.reference_name, legacy_column
			).where(
				legacy_column.notnull()
				& (legacy_column != "")
				& (table.reference_name.isnull() | (table.reference_name == ""))
			).run()

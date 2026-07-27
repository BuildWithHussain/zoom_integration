import frappe

DOCTYPES = {
	"Zoom Webinar Registration": "Zoom Session Registration",
	"Zoom Webinar Attendance Record": "Zoom Session Attendance Record",
	"Zoom Webinar Additional Param": "Zoom Session Additional Param",
}


def execute():
	"""These doctypes now hold meeting rows as well as webinar rows, so drop `Webinar`
	from their names.

	Runs pre_model_sync: after the model sync the new names already exist as empty
	tables built from the renamed JSON, and the rename would fail on a name clash.
	"""
	for old, new in DOCTYPES.items():
		if frappe.db.exists("DocType", old) and not frappe.db.exists("DocType", new):
			frappe.rename_doc("DocType", old, new, force=True, show_alert=False)

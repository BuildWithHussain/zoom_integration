import frappe


def execute():
	"""Rename Zoom Meetings created before the doctype was named by zoom_meeting_id.

	rename_doc repoints Link fields (Buzz Event.zoom_meeting) and Dynamic Links
	(reference_name on the session registration and attendance records).
	"""
	meetings = frappe.get_all(
		"Zoom Meeting", fields=["name", "zoom_meeting_id"], filters={"zoom_meeting_id": ["is", "set"]}
	)

	for meeting in meetings:
		if meeting.name == meeting.zoom_meeting_id:
			continue
		if frappe.db.exists("Zoom Meeting", meeting.zoom_meeting_id):
			frappe.log_error(
				f"Cannot rename Zoom Meeting {meeting.name}: {meeting.zoom_meeting_id} already exists"
			)
			continue

		frappe.rename_doc("Zoom Meeting", meeting.name, meeting.zoom_meeting_id, force=True, show_alert=False)

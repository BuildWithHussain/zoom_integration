// Copyright (c) 2025, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Zoom Webinar", {
	refresh(frm) {
		if (!frm.doc.__islocal && !frm.doc.attendance_synced) {
			frm.add_custom_button(__("Sync Attendance"), () => {
				frm.call({
					method: "sync_attendance",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Syncing Attendance..."),
				}).then(() => frm.reload_doc());
			});
		}
	},
});

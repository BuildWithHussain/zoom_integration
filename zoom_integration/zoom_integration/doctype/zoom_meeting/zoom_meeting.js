// Copyright (c) 2026, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Zoom Meeting", {
	refresh(frm) {
		frm.fields_dict.timezone.set_data(zoom_integration.timezones);
		if (!frm.doc.__islocal) {
			frm.add_custom_button(__("Sync Attendance"), () => {
				frm.call({
					method: "sync_attendance_in_background",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Starting attendance sync..."),
				}).then(() => {
					frappe.show_alert({
						message: __("Attendance sync has been started in the background..."),
						indicator: "green",
					});
				});
			});
		}
	},
});

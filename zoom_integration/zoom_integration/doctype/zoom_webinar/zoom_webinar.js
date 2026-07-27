// Copyright (c) 2025, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Zoom Webinar", {
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
			frm.add_custom_button(__("Sync Registrations"), () => {
				frm.call({
					method: "sync_registrations_in_background",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Starting registrations sync..."),
				}).then(() => {
					frappe.show_alert({
						message: __("Registration sync has been started in the background..."),
						indicator: "green",
					});
				});
			});
		}
	},
});

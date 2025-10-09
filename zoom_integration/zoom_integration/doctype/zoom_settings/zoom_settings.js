// Copyright (c) 2025, Build With Hussain and contributors
// For license information, please see license.txt

frappe.ui.form.on("Zoom Settings", {
	refresh(frm) {
		frm.add_custom_button(
			__("Sync Webinar Templates"),
			() => {
				frm.call({
					method: "sync_webinar_templates",
					doc: frm.doc,
					freeze: true,
					freeze_message: __("Syncing webinar templates..."),
				}).then(() => {
					frappe.show_alert({
						message: __("Webinar templates Synced!"),
						indicator: "green",
					});
				});
			}
		)
	},
});

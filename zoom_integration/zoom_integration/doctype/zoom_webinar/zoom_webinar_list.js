frappe.listview_settings['Zoom Webinar'] = {
	// add custom button
	onload(listview) {


		const btn = listview.page.add_inner_button(__("Add Existing from Zoom"), () => {
			frappe.call({method: "zoom_integration.utils.get_upcoming_webinars", btn}).then((r) => {
				const webinars = r.message;
				// get webinar id
				frappe.prompt(
					[
						{
							label: "Webinar ID",
							fieldname: "webinar_id",
							fieldtype: "Select",
							reqd: 1,
							options: webinars.map((webinar) => ({
								label: `${webinar.topic} (${webinar.id})`,
								value: webinar.id,
							})),
						},
					],
					(values) => {
						frappe.call({
							method: "zoom_integration.zoom_integration.doctype.zoom_webinar.zoom_webinar.import_existing_webinar",
							args: {
								webinar_id: values.webinar_id,
							},
							freeze: true,
							freeze_message: __("Adding Webinar..."),
						}).then(() => listview.refresh());
					}
				);
			});
		});


	}
}

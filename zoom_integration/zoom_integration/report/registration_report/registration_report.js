// Copyright (c) 2026, Build With Hussain and contributors
// For license information, please see license.txt

frappe.query_reports["Registration Report"] = {
	filters: [
		{
			fieldname: "webinar",
			label: __("Webinar"),
			fieldtype: "Link",
			options: "Zoom Webinar",
			reqd: 1,
		},
	],
};

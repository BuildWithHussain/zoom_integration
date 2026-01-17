# Copyright (c) 2026, Build With Hussain
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters or {})
	return columns, data


def get_columns():
	return [
		{
			"label": _("User Email"),
			"fieldname": "user",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("First Name"),
			"fieldname": "first_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Last Name"),
			"fieldname": "last_name",
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"label": _("Synced from Zoom"),
			"fieldname": "synced_from_zoom",
			"fieldtype": "Check",
			"width": 200,
		},
		{
			"label": _("Auto Registered"),
			"fieldname": "custom_auto_registered",
			"fieldtype": "Check",
			"width": 200,
		},
		{
			"label": _("Registrant ID"),
			"fieldname": "registrant_id",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("Join URL"),
			"fieldname": "join_url",
			"fieldtype": "Data",
			"width": 200,
		},
		{
			"label": _("UTM Source"),
			"fieldname": "utm_source",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("UTM Medium"),
			"fieldname": "utm_medium",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("UTM Campaign"),
			"fieldname": "utm_campaign",
			"fieldtype": "Data",
			"width": 150,
		},
		{
			"label": _("UTM Term"),
			"fieldname": "utm_term",
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"label": _("UTM Content"),
			"fieldname": "utm_content",
			"fieldtype": "Data",
			"width": 120,
		},
	]


def get_data(filters):
	values = {"webinar": filters.get("webinar")}

	# Base registration data
	query = """
		SELECT
			zwreg.name AS registration,
			zwreg.user,
			zwreg.first_name,
			zwreg.last_name,
			zwreg.synced_from_zoom,
			zwreg.registrant_id,
			zwreg.join_url,
			zwreg.custom_auto_registered
		FROM `tabZoom Webinar Registration` zwreg
		WHERE zwreg.webinar = %(webinar)s
		ORDER BY zwreg.user
	"""

	records = frappe.db.sql(query, values, as_dict=True)

	if not records:
		return []

	registration_names = [r["registration"] for r in records]

	# Fetch UTM parameters
	utm_query = """
		SELECT
			parent,
			`key`,
			value
		FROM `tabUtm Parameters`
		WHERE
			parenttype = 'Zoom Webinar Registration'
			AND parent IN %(parents)s
	"""

	utm_rows = frappe.db.sql(
		utm_query,
		{"parents": tuple(registration_names)},
		as_dict=True,
	)

	utm_map = {}
	for row in utm_rows:
		utm_map.setdefault(row.parent, {})[row.key] = row.value

	# Merge UTM data into records
	for record in records:
		utm = utm_map.get(record["registration"], {})
		record["utm_source"] = utm.get("utm_source", "")
		record["utm_medium"] = utm.get("utm_medium", "")
		record["utm_campaign"] = utm.get("utm_campaign", "")
		record["utm_term"] = utm.get("utm_term", "")
		record["utm_content"] = utm.get("utm_content", "")

		# Cleanup
		record.pop("registration", None)

	return records

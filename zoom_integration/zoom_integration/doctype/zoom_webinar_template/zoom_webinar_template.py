# Copyright (c) 2025, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe.model.document import Document

from zoom_integration.utils import ZOOM_API_BASE_PATH, get_authenticated_headers_for_zoom


class ZoomWebinarTemplate(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		id: DF.Data | None
		title: DF.Data
		type: DF.Int
	# end: auto-generated types

	pass


def sync_templates_from_zoom():
	url = f"{ZOOM_API_BASE_PATH}/users/me/webinar_templates"
	headers = get_authenticated_headers_for_zoom()
	templates = requests.get(url, headers=headers).json()

	if templates.get("templates"):
		for template in templates.get("templates"):
			print(template)
			if not frappe.db.exists("Zoom Webinar Template", {"id": template.get("id")}):
				doc = frappe.get_doc(
					{
						"doctype": "Zoom Webinar Template",
						"id": template.get("id"),
						"title": template.get("name"),
						"type": template.get("type"),
					}
				)
				doc.insert(ignore_permissions=True)



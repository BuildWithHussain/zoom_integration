# Copyright (c) 2025, Build With Hussain and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ZoomWebinarRegistrantRecord(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from zoom_integration.zoom_integration.doctype.zoom_webinar_additional_param.zoom_webinar_additional_param import (
			ZoomWebinarAdditionalParam,
		)

		amended_from: DF.Link | None
		custom_question: DF.Table[ZoomWebinarAdditionalParam]
		email: DF.Data | None
		first_name: DF.Data | None
		last_name: DF.Data | None
		phone: DF.Data | None
		registrant_id: DF.Data | None
		webinar: DF.Link | None
	# end: auto-generated types

	pass

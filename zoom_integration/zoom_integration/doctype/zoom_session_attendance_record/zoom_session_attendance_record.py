# Copyright (c) 2025, Build With Hussain and contributors
# For license information, please see license.txt

from frappe.model.document import Document

from zoom_integration.utils import validate_session_reference


class ZoomSessionAttendanceRecord(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		full_name: DF.Data | None
		reference_doctype: DF.Link
		reference_name: DF.DynamicLink
		registrant_id: DF.Data | None
		registration: DF.Link | None
		total_duration: DF.Duration
		user_email: DF.Data
	# end: auto-generated types

	def validate(self):
		validate_session_reference(self)

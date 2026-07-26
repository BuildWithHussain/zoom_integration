# Copyright (c) 2025, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ZoomSessionAttendanceRecord(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		full_name: DF.Data | None
		meeting: DF.Link | None
		registrant_id: DF.Data | None
		registration: DF.Link | None
		total_duration: DF.Duration
		user_email: DF.Data
		webinar: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if bool(self.webinar) == bool(self.meeting):
			frappe.throw(_("Set exactly one of Webinar or Meeting."))

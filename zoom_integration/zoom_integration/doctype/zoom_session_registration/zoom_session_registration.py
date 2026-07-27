# Copyright (c) 2025, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class ZoomSessionRegistration(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from zoom_integration.zoom_integration.doctype.zoom_session_additional_param.zoom_session_additional_param import (
			ZoomSessionAdditionalParam,
		)

		additional_params: DF.Table[ZoomSessionAdditionalParam]
		amended_from: DF.Link | None
		email: DF.Data | None
		first_name: DF.Data | None
		join_url: DF.Data | None
		last_name: DF.Data | None
		meeting: DF.Link | None
		registrant_id: DF.Data | None
		synced_from_zoom: DF.Check
		user: DF.Link | None
		webinar: DF.Link | None
	# end: auto-generated types

	def validate(self):
		if bool(self.webinar) == bool(self.meeting):
			frappe.throw(_("Set exactly one of Webinar or Meeting."))

	def before_insert(self):
		if not (self.user or self.email):
			self.user = frappe.session.user

		if self.email:
			user_exists = frappe.db.exists("User", {"email": self.email})
			self.user = user_exists

		if self.user == "Guest":
			frappe.throw(_("Guest user cannot register for a Zoom session"))
		elif self.user and not self.email:
			user_doc = frappe.get_cached_doc("User", self.user)
			self.email = user_doc.email
			self.first_name = user_doc.first_name
			self.last_name = user_doc.last_name

	def before_submit(self):
		if self.synced_from_zoom:
			# this was already synced from zoom, no need to register again
			return

		additional_params = {}
		if self.additional_params:
			additional_params = {param.key: param.value for param in self.additional_params}

		# validate() guarantees exactly one of meeting/webinar is set
		session = frappe.get_cached_doc(
			"Zoom Meeting" if self.meeting else "Zoom Webinar", self.meeting or self.webinar
		)

		registration = session.add_registrant(self.email, self.first_name, self.last_name, additional_params)

		self.join_url = registration.get("join_url")
		self.registrant_id = registration.get("registrant_id")

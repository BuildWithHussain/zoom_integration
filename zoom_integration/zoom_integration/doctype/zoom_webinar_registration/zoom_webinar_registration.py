# Copyright (c) 2025, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ZoomWebinarRegistration(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from zoom_integration.zoom_integration.doctype.zoom_webinar_additional_param.zoom_webinar_additional_param import (
			ZoomWebinarAdditionalParam,
		)

		additional_params: DF.Table[ZoomWebinarAdditionalParam]
		amended_from: DF.Link | None
		email: DF.Data | None
		first_name: DF.Data | None
		join_url: DF.Data | None
		last_name: DF.Data | None
		registrant_id: DF.Data | None
		synced_from_zoom: DF.Check
		user: DF.Link | None
		webinar: DF.Link
	# end: auto-generated types

	def before_insert(self):
		if not (self.user or self.email):
			self.user = frappe.session.user

		if self.email:
			user_exists = frappe.db.exists("User", {"email": self.email})
			self.user = user_exists

		if self.user == "Guest":
			frappe.throw("Guest user cannot register for webinar")
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

		registration = frappe.get_cached_doc("Zoom Webinar", self.webinar).add_registrant(
			self.email, self.first_name, self.last_name, additional_params
		)

		self.join_url = registration.get("join_url")
		self.registrant_id = registration.get("registrant_id")

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

		amended_from: DF.Link | None
		join_url: DF.Data | None
		registrant_id: DF.Data | None
		user: DF.Link | None
		webinar: DF.Link
	# end: auto-generated types

	def before_insert(self):
		if not self.user:
			self.user = frappe.session.user

		if self.user == "Guest":
			frappe.throw("Guest user cannot register for webinar")


	def before_submit(self):
		user_doc = frappe.get_cached_doc("User", self.user)
		registration = frappe.get_cached_doc("Zoom Webinar", self.webinar).add_registrant(
			user_doc.email, user_doc.first_name, user_doc.last_name
		)

		self.join_url = registration.get("join_url")
		self.registrant_id = registration.get("registrant_id")

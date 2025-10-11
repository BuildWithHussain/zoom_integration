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
		id: DF.Data | None
		join_url: DF.Data | None
		registrant_id: DF.Data | None
		user: DF.Link | None
		webinar: DF.Link
	# end: auto-generated types

	def before_insert(self):
		if not self.user:
			self.user = frappe.session.user

		email = frappe.db.get_value("User", self.user, "email")
		if email == "Guest":
			frappe.throw("Guest users cannot register for webinars. Please log in first.")

		user_doc = frappe.get_cached_doc("User", email)

		registration = frappe.get_doc("Zoom Webinar", self.webinar).add_registrant(
			email, user_doc.first_name, user_doc.last_name
		)

		self.user = email
		self.id = registration.get("id")
		self.join_url = registration.get("join_url")
		self.registrant_id = registration.get("registrant_id")
		self.docstatus = 1


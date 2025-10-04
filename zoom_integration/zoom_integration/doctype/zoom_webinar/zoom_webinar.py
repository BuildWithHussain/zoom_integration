# Copyright (c) 2025, Build With Hussain and contributors
# For license information, please see license.txt

import json

import frappe
import requests
from frappe.model.document import Document
from frappe.utils import cint, format_datetime

from zoom_integration.utils import ZOOM_API_BASE_PATH, get_authenticated_headers_for_zoom


class ZoomWebinar(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		agenda: DF.SmallText | None
		date: DF.Date
		description: DF.TextEditor | None
		duration: DF.Duration
		send_zoom_registration_email: DF.Check
		start_time: DF.Time
		title: DF.Data
		zoom_link: DF.Data | None
		zoom_webinar_id: DF.Data | None
	# end: auto-generated types

	def before_insert(self):
		self.create_webinar_on_zoom()

	def create_webinar_on_zoom(self):
		url = f"{ZOOM_API_BASE_PATH}/users/me/webinars"
		headers = get_authenticated_headers_for_zoom()
		body = json.dumps(
			{
				"topic": self.title,
				"agenda": self.agenda or self.title,
				"type": 5,  # Scheduled webinar
				"duration": cint(self.duration / 60) if self.duration else 60,
				"start_time": format_datetime(f"{self.date} {self.start_time}", "yyyy-MM-ddTHH:mm:ssZ"),
				"settings": {
					"host_video": True,
					"panelists_video": True,
					"practice_session": True,
					"hd_video": True,
					"approval_type": 0,  # Automatically approve
					"registration_type": 1,  # Register once and join anytime
					"audio": "both",  # Both telephony and VoIP
					"auto_recording": "cloud",  # Record webinar in the cloud, TODO: make this configurable
					"meeting_authentication": False,  # Disable authentication for simplicity
				},
				"registrants_email_notification": self.send_zoom_registration_email,
			}
		)

		response = requests.post(url, headers=headers, data=body)
		if response.status_code == 201:
			data = response.json()
			self.zoom_link = data.get("join_url")
			self.zoom_webinar_id = data.get("id")
			frappe.msgprint("Webinar created successfully on Zoom.")
		else:
			frappe.throw("Failed to create webinar on Zoom: {0}".format(response.text))

	def on_trash(self):
		if self.zoom_webinar_id:
			self.delete_webinar_on_zoom()

		# frappe.db.delete("Zoom Webinar Registration", {"webinar": self.name})

	def delete_webinar_on_zoom(self):
		url = f"{ZOOM_API_BASE_PATH}/webinars/{self.zoom_webinar_id}"
		headers = get_authenticated_headers_for_zoom()

		response = requests.delete(url, headers=headers)
		if response.status_code == 204:
			self.zoom_link = None
			self.zoom_webinar_id = None
			self.save()
			frappe.msgprint(frappe._("Webinar deleted successfully from Zoom."))
		else:
			frappe.throw(frappe._(f"Failed to delete webinar: {response.text}"))

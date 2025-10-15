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
		attendance_synced: DF.Check
		date: DF.Date
		description: DF.TextEditor | None
		duration: DF.Duration
		send_zoom_registration_email: DF.Check
		start_time: DF.Time
		template: DF.Link | None
		title: DF.Data
		zoom_link: DF.Data | None
		zoom_webinar_id: DF.Data | None
	# end: auto-generated types

	def before_insert(self):
		self.create_webinar_on_zoom()

	def create_webinar_on_zoom(self):
		if self.zoom_webinar_id:
			return  # Webinar already created on Zoom

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
				"template_id": self.template or None,
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

	def on_update(self):
		if not self.zoom_webinar_id:
			return
		self.update_webinar_on_zoom_if_applicable()

	def update_webinar_on_zoom_if_applicable(self):
		# For simplicity, we will only update the title and agenda in this example.
		url = f"{ZOOM_API_BASE_PATH}/webinars/{self.zoom_webinar_id}"
		headers = get_authenticated_headers_for_zoom()
		body = json.dumps(
			{
				"topic": self.title,
				"agenda": self.agenda or self.title,
				"duration": cint(self.duration / 60) if self.duration else 60,
				"start_time": format_datetime(f"{self.date} {self.start_time}", "yyyy-MM-ddTHH:mm:ssZ"),
			}
		)

		response = requests.patch(url, headers=headers, data=body)
		if response.status_code == 204:
			frappe.msgprint("Webinar updated successfully on Zoom.")
		else:
			frappe.throw("Failed to update webinar on Zoom: {0}".format(response.text))

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

	def add_registrant(self, email: str, first_name: str, last_name: str | None = None):
		if not self.zoom_webinar_id:
			frappe.throw(frappe._("Webinar not created on Zoom yet."))

		url = f"{ZOOM_API_BASE_PATH}/webinars/{self.zoom_webinar_id}/registrants"
		headers = get_authenticated_headers_for_zoom()
		body = json.dumps(
			{
				"email": email,
				"first_name": first_name,
				"last_name": last_name or "N/A",
			}
		)

		response = requests.post(url, headers=headers, data=body)
		if response.status_code == 201:
			data = response.json()
			return data
		else:
			frappe.throw(frappe._(f"Failed to add registrant: {response.text}"))

	@frappe.whitelist()
	def sync_attendance(self):
		details = get_webinar_attendance_details(self.name)

		for attendance in details:
			registration = frappe.db.get_value("Zoom Webinar Registration", {"user": attendance.get("user_email", "N/A")}, "name")

			frappe.get_doc(
				{
					"doctype": "Zoom Webinar Attendance Record",
					"registration": registration,
					"webinar": self.name,
					"user_email": attendance.get("user_email"),
					"name": attendance.get("name"),
					"total_duration": attendance.get("total_duration"),
				}
			).insert(ignore_permissions=True, ignore_if_duplicate=True).submit()

		self.attendance_synced = 1
		self.save()

def get_webinar_attendance_details(webinar_id: str, limit: int = 1000):
	url = f"{ZOOM_API_BASE_PATH}/past_webinars/{webinar_id}/participants?page_size={limit}"
	headers = get_authenticated_headers_for_zoom()
	response = requests.get(url, headers=headers)

	if response.status_code == 200:
		data = response.json()
		attendance_details = data.get("participants", [])

		if data.get("total_records", 0) > 1000:
			frappe.throw(
				"Attendance details exceed the limit of 300 participants. Pagination not implemented yet."
			)

		# process the attendance to sum the duration based on user email
		# since the same user can join multiple times, we will sum their durations
		attendance_summary = {}
		for participant in attendance_details:
			email = participant.get("user_email")
			if email:
				if email not in attendance_summary:
					attendance_summary[email] = {
						"name": participant.get("name"),
						"total_duration": 0,
						"registrant_id": participant.get("registrant_id"),
					}
				attendance_summary[email]["total_duration"] += participant.get("duration", 0)

		# Convert the summary to a list of dictionaries
		attendance_details = [
			{
				"user_email": email,
				"name": details["name"],
				"total_duration": details["total_duration"],
			}
			for email, details in attendance_summary.items()
		]
		# Sort by total duration in descending order
		attendance_details.sort(key=lambda x: x["total_duration"], reverse=True)

		return attendance_details
	else:
		frappe.throw(f"Failed to fetch webinar attendance details: {response.text}")


@frappe.whitelist()
def import_existing_webinar(webinar_id: str):
	if not webinar_id:
		frappe.throw("Webinar ID is required.")

	# Check if the webinar already exists in the system
	existing = frappe.db.get_value("Zoom Webinar", {"zoom_webinar_id": webinar_id})
	if existing:
		frappe.msgprint("Webinar already exists in the system.")
		return existing

	url = f"{ZOOM_API_BASE_PATH}/webinars/{webinar_id}"
	headers = get_authenticated_headers_for_zoom()
	response = requests.get(url, headers=headers)

	if response.status_code == 200:
		data = response.json()
		webinar = frappe.get_doc(
			{
				"doctype": "Zoom Webinar",
				"title": data.get("topic"),
				"agenda": data.get("agenda") or data.get("topic"),
				"date": data.get("start_time", "").split("T")[0] if data.get("start_time") else None,
				"start_time": data.get("start_time", "").split("T")[1].replace("Z", "") if data.get("start_time") else None,
				"duration": data.get("duration", 60) * 60,  # Convert minutes to seconds
				"zoom_webinar_id": data.get("id"),
				"zoom_link": data.get("join_url"),
			}
		)
		webinar.insert(ignore_permissions=True)
		frappe.msgprint("Webinar imported successfully from Zoom.")
		return webinar.name
	else:
		frappe.throw(f"Failed to fetch webinar details: {response.text}")

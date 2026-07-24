# Copyright (c) 2026, Build With Hussain and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, format_datetime, get_time

from zoom_integration.api import (
	add_zoom_registrant,
	create_zoom_session,
	delete_zoom_session,
	get_zoom_participants,
	update_zoom_session,
)

RESOURCE = "meetings"


class ZoomMeeting(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		agenda: DF.SmallText | None
		attendance_synced: DF.Check
		date: DF.Date
		duration: DF.Duration
		send_zoom_registration_email: DF.Check
		start_time: DF.Time
		timezone: DF.Autocomplete | None
		title: DF.Data
		zoom_link: DF.Data | None
		zoom_meeting_id: DF.Data | None
		zoom_meeting_uuid: DF.Data | None
	# end: auto-generated types

	def before_insert(self):
		self.create_meeting_on_zoom()

	def create_meeting_on_zoom(self):
		if self.zoom_meeting_id:
			return

		body = {
			"topic": self.title,
			"agenda": self.agenda or self.title,
			"type": 2,  # Scheduled meeting
			"duration": cint(self.duration / 60) if self.duration else 60,
			"start_time": format_datetime(f"{self.date} {self.start_time}", "yyyy-MM-ddTHH:mm:ss"),
			"timezone": self.timezone or "Asia/Calcutta",
			"settings": {
				"host_video": True,
				"participant_video": True,
				"join_before_host": False,
				"approval_type": 0,  # Automatically approve registrants (required for registration)
				"registration_type": 1,  # Register once and join anytime
				"audio": "both",
				"auto_recording": "cloud",
				"meeting_authentication": False,
			},
			"registrants_email_notification": bool(self.send_zoom_registration_email),
		}

		data = create_zoom_session(RESOURCE, body)
		self.zoom_link = data.get("join_url")
		self.zoom_meeting_id = str(data.get("id")) if data.get("id") is not None else None
		self.zoom_meeting_uuid = data.get("uuid")
		frappe.msgprint(_("Meeting created successfully on Zoom."))

	def on_update(self):
		if not self.zoom_meeting_id:
			return
		self.update_meeting_on_zoom_if_applicable()

	def update_meeting_on_zoom_if_applicable(self):
		if self.flags.in_import or self.flags.in_migration or self.is_new():
			return

		before_save = self.get_doc_before_save()
		if not before_save:
			return

		unchanged = (
			self.title == before_save.title
			and self.agenda == before_save.agenda
			and self.duration == before_save.duration
			and self.timezone == before_save.timezone
			and self.get("date") == str(before_save.get("date"))
			and get_time(self.get("start_time")) == get_time(before_save.get("start_time"))
		)
		if unchanged:
			return

		body = {
			"topic": self.title,
			"agenda": self.agenda or self.title,
			"duration": cint(self.duration / 60) if self.duration else 60,
			"start_time": format_datetime(f"{self.date} {self.start_time}", "yyyy-MM-ddTHH:mm:ss"),
			"timezone": self.timezone or "Asia/Calcutta",
		}
		update_zoom_session(RESOURCE, self.zoom_meeting_id, body)
		frappe.msgprint(_("Meeting updated successfully on Zoom."))

	def on_trash(self):
		if not self.zoom_meeting_id:
			return
		deleted = delete_zoom_session(RESOURCE, self.zoom_meeting_id)
		if not deleted:
			frappe.msgprint(_("Meeting not found on Zoom (already deleted). Clearing local reference."))

	def add_registrant(
		self, email: str, first_name: str, last_name: str | None = None, additional_params: dict | None = None
	) -> dict:
		if not self.zoom_meeting_id:
			frappe.throw(_("Meeting not created on Zoom yet."))

		body = {
			"email": email,
			"first_name": first_name,
			"last_name": last_name or "N/A",
			**(additional_params or {}),
		}
		return add_zoom_registrant(RESOURCE, self.zoom_meeting_id, body)

	@frappe.whitelist()
	def sync_attendance(self):
		if not self.zoom_meeting_uuid:
			frappe.throw(_("Meeting has not run yet (no UUID to fetch attendance for)."))

		participants = get_zoom_participants(RESOURCE, self.zoom_meeting_uuid)

		# Same user can join multiple times; sum durations per email.
		summary: dict[str, dict] = {}
		for participant in participants:
			email = participant.get("user_email")
			if not email:
				continue
			entry = summary.setdefault(
				email,
				{
					"name": participant.get("name"),
					"total_duration": 0,
					"registrant_id": participant.get("registrant_id"),
				},
			)
			entry["total_duration"] += participant.get("duration", 0)

		for email, details in summary.items():
			if frappe.db.exists("Zoom Webinar Attendance Record", {"meeting": self.name, "user_email": email}):
				continue
			frappe.get_doc(
				{
					"doctype": "Zoom Webinar Attendance Record",
					"meeting": self.name,
					"user_email": email,
					"full_name": details["name"],
					"total_duration": details["total_duration"],
					"registrant_id": details["registrant_id"],
					"docstatus": 1,
				}
			).insert(ignore_permissions=True)

		self.db_set("attendance_synced", 1)
		frappe.msgprint(_("Synced attendance for {0} participants.").format(len(summary)))

	@frappe.whitelist()
	def sync_attendance_in_background(self):
		frappe.enqueue_doc(self.doctype, self.name, "sync_attendance", queue="long")

import base64

import frappe
import requests
from frappe import _

ZOOM_API_BASE_PATH = "https://api.zoom.us/v2"

SESSION_DOCTYPES = ("Zoom Meeting", "Zoom Webinar")


def validate_session_reference(doc):
	"""link_filters narrows the desk picker client-side only, so guard it here too."""
	if doc.reference_doctype not in SESSION_DOCTYPES:
		frappe.throw(
			_("Session Type must be one of {0}.").format(", ".join(SESSION_DOCTYPES)),
			title=_("Invalid Session Type"),
		)


def authenticate():
	zoom = frappe.get_single("Zoom Settings")

	if not (
		zoom.client_id
		and zoom.get_password(fieldname="client_secret", raise_exception=False)
		and zoom.account_id
	):
		frappe.throw(
			_("Please set Zoom Client ID, Client Secret and Account ID in Zoom Settings."),
			title=_("Zoom Settings Incomplete"),
		)

	authenticate_url = (
		f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={zoom.account_id}"
	)

	headers = {
		"Authorization": "Basic "
		+ base64.b64encode(
			bytes(
				zoom.client_id + ":" + zoom.get_password(fieldname="client_secret", raise_exception=False),
				encoding="utf8",
			)
		).decode()
	}
	response = requests.request("POST", authenticate_url, headers=headers)
	return response.json()["access_token"]


def get_authenticated_headers_for_zoom():
	return {
		"Authorization": "Bearer " + authenticate(),
		"content-type": "application/json",
	}


@frappe.whitelist()
def get_upcoming_webinars():
	url = f"{ZOOM_API_BASE_PATH}/users/me/webinars?type=upcoming"
	headers = get_authenticated_headers_for_zoom()
	response = requests.get(url, headers=headers)

	if response.status_code == 200:
		data = response.json()
		return data.get("webinars", [])
	else:
		frappe.throw(f"Failed to fetch upcoming webinars: {response.text}")

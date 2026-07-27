"""Realistic Zoom API response fixtures. Shapes mirror the live Zoom v2 API
so mocks behave like production. Reused by all zoom_integration tests."""

import random
import string

CREATE_MEETING_RESPONSE = {
	"uuid": "aDEFghiJKLmno12PQ==",
	"id": 91234567890,
	"host_id": "hostAbc123",
	"topic": "Test Meeting",
	"type": 2,
	"status": "waiting",
	"start_time": "2026-08-01T10:00:00Z",
	"duration": 60,
	"timezone": "Asia/Calcutta",
	"created_at": "2026-07-24T09:00:00Z",
	"join_url": "https://zoom.us/j/91234567890?pwd=xYzToken",
	"start_url": "https://zoom.us/s/91234567890?zak=zakToken",
	"password": "aB3dEf",
	"settings": {"approval_type": 0, "registration_type": 1, "audio": "both"},
}


CREATE_WEBINAR_RESPONSE = {
	"uuid": "bXYZabcDEFghi34RS==",
	"id": 81234567890,
	"host_id": "hostAbc123",
	"topic": "Test Webinar",
	"type": 5,
	"start_time": "2026-08-01T10:00:00Z",
	"duration": 60,
	"timezone": "Asia/Calcutta",
	"created_at": "2026-07-24T09:00:00Z",
	"join_url": "https://zoom.us/w/81234567890?pwd=wEbToken",
	"start_url": "https://zoom.us/s/81234567890?zak=zakToken",
	"settings": {"approval_type": 0, "registration_type": 1, "audio": "both"},
}


# PATCH /meetings/{id} and DELETE /meetings/{id} return 204 with an empty body.

ADD_MEETING_REGISTRANT_RESPONSE = {
	"id": 91234567890,
	"topic": "Test Meeting",
	"registrant_id": "abcDEF12ghIJ",
	"start_time": "2026-08-01T10:00:00Z",
	"join_url": "https://zoom.us/w/91234567890?tk=regToken&pwd=xYz",
}

ADD_WEBINAR_REGISTRANT_RESPONSE = {
	"id": 81234567890,
	"topic": "Test Webinar",
	"registrant_id": "webREG123456",
	"start_time": "2026-08-01T10:00:00Z",
	"join_url": "https://zoom.us/w/81234567890?tk=webRegToken",
}

WEBINAR_PARTICIPANTS = [
	{
		"name": "Carol",
		"user_email": "carol@example.com",
		"total_duration": 3100,
		"registrant_id": "webREG123456",
	},
	{
		"name": "Dan",
		"user_email": "dan@example.com",
		"total_duration": 2400,
		"registrant_id": "webREG789012",
	},
]

WEBINAR_REGISTRANTS = [
	{
		"id": "webREG123456",
		"email": "carol@example.com",
		"first_name": "Carol",
		"last_name": "Diaz",
		"join_url": "https://zoom.us/w/81234567890?tk=webRegToken",
		"custom_questions": [],
	}
]

MEETING_REGISTRANTS_LIST_RESPONSE = {
	"page_count": 1,
	"page_size": 300,
	"total_records": 1,
	"next_page_token": "",
	"registrants": [
		{
			"id": "abcDEF12ghIJ",
			"email": "alice@example.com",
			"first_name": "Alice",
			"last_name": "Smith",
			"status": "approved",
			"create_time": "2026-07-24T09:10:00Z",
			"join_url": "https://zoom.us/w/91234567890?tk=regToken",
			"custom_questions": [],
		}
	],
}

MEETING_PARTICIPANTS_RESPONSE = {
	"page_count": 1,
	"page_size": 300,
	"total_records": 2,
	"next_page_token": "",
	"participants": [
		{
			"id": "",
			"user_id": "16778240",
			"name": "Alice",
			"user_email": "alice@example.com",
			"join_time": "2026-08-01T10:01:00Z",
			"leave_time": "2026-08-01T10:55:00Z",
			"duration": 3240,
			"registrant_id": "abcDEF12ghIJ",
		},
		{
			"id": "",
			"user_id": "16778241",
			"name": "Bob",
			"user_email": "bob@example.com",
			"join_time": "2026-08-01T10:05:00Z",
			"leave_time": "2026-08-01T10:50:00Z",
			"duration": 2700,
			"registrant_id": "klmNOP34qrST",
		},
	],
}

# Zoom "resource not found on delete" error body.
NOT_FOUND_DELETE_RESPONSE = {"code": 3001, "message": "Meeting does not exist."}


# Sessions are named by Zoom ID and registrant_id is unique, but test rows survive a run,
# so fixed IDs collide with their own leftovers. Assertions read these back off the
# response, so drawing them fresh costs no reproducibility.
def _zoom_id(prefix: int) -> int:
	return int(f"{prefix}{random.randrange(10**9):09d}")


def _registrant_id() -> str:
	return "".join(random.choices(string.ascii_letters + string.digits, k=12))


def create_meeting_response(meeting_id=None):
	return {**CREATE_MEETING_RESPONSE, "id": meeting_id or _zoom_id(9)}


def create_webinar_response(webinar_id=None):
	return {**CREATE_WEBINAR_RESPONSE, "id": webinar_id or _zoom_id(8)}


def add_meeting_registrant_response(registrant_id=None):
	return {**ADD_MEETING_REGISTRANT_RESPONSE, "registrant_id": registrant_id or _registrant_id()}


def add_webinar_registrant_response(registrant_id=None):
	return {**ADD_WEBINAR_REGISTRANT_RESPONSE, "registrant_id": registrant_id or _registrant_id()}


def webinar_registrants(registrant_id=None):
	return [{**WEBINAR_REGISTRANTS[0], "id": registrant_id or _registrant_id()}]


def mock_response(status_code, json_data=None, text=""):
	"""Build a fake requests.Response-like object for patching."""
	from unittest.mock import MagicMock

	resp = MagicMock()
	resp.status_code = status_code
	resp.json.return_value = json_data if json_data is not None else {}
	resp.text = text or ""
	resp.headers = {}
	return resp

"""Realistic Zoom API response fixtures. Shapes mirror the live Zoom v2 API
so mocks behave like production. Reused by all zoom_integration tests."""

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


def create_meeting_response(meeting_id):
	"""Zoom Meeting is named after its Zoom ID, so tests sharing a class need distinct IDs."""
	return {**CREATE_MEETING_RESPONSE, "id": int(meeting_id)}


# PATCH /meetings/{id} and DELETE /meetings/{id} return 204 with an empty body.

ADD_MEETING_REGISTRANT_RESPONSE = {
	"id": 91234567890,
	"topic": "Test Meeting",
	"registrant_id": "abcDEF12ghIJ",
	"start_time": "2026-08-01T10:00:00Z",
	"join_url": "https://zoom.us/w/91234567890?tk=regToken&pwd=xYz",
}

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


def mock_response(status_code, json_data=None, text=""):
	"""Build a fake requests.Response-like object for patching."""
	from unittest.mock import MagicMock

	resp = MagicMock()
	resp.status_code = status_code
	resp.json.return_value = json_data if json_data is not None else {}
	resp.text = text or ""
	resp.headers = {}
	return resp

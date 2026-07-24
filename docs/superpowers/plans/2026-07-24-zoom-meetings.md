# Zoom Meetings Support (zoom_integration) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add first-class Zoom **Meeting** support alongside the existing Webinar support, so a Zoom Meeting can be created/updated/deleted, registrants added, and attendance synced — reusing shared API helpers instead of duplicating the Webinar controller.

**Architecture:** Extract the resource-parameterized HTTP calls into a new `zoom_integration/api.py` (functions take `resource="meetings"|"webinars"`). Add a `Zoom Meeting` DocType whose controller delegates to those helpers. Make the existing `Zoom Webinar Registration` and `Zoom Webinar Attendance Record` doctypes reference **either** a webinar or a meeting via an additive optional `meeting` link (no migration of existing rows). The existing `Zoom Webinar` controller is left untouched (working code, out of scope to refactor).

**Tech Stack:** Frappe Framework (Python), `requests`, `unittest.mock` for patching the Zoom HTTP seam, `frappe.tests.IntegrationTestCase`.

## Global Constraints

- Branch: `feat/zoom-meetings` off `main`. All work on this branch.
- Tabs for indentation (match existing files).
- Zoom Server-to-Server OAuth is already configured in `Zoom Settings`; auth is via `zoom_integration.utils.get_authenticated_headers_for_zoom()` — never call the network in tests, always patch this and `requests`.
- Meeting `type` is `2` (scheduled meeting). Registrants require `settings.approval_type: 0` in the create body.
- Meeting **participant** reports use the meeting **UUID** (`past_meetings/{uuid}`), not the numeric id. Create/update/delete/registrants use the numeric id.
- Mock return values must mirror real Zoom API JSON (shapes fixed in Task 1, reused everywhere).
- Run tests with: `bench --site buzz.localhost run-tests --app zoom_integration --module <dotted.module.path>` (ask user for site if `buzz.localhost` missing). Credentials Administrator/admin.
- After any doctype schema change: `bench --site buzz.localhost migrate`.

---

### Task 1: Shared Zoom API helpers (`api.py`)

Resource-parameterized functions all controllers call. Fully mockable at `zoom_integration.api.requests` + `zoom_integration.api.get_authenticated_headers_for_zoom`.

**Files:**
- Create: `zoom_integration/api.py`
- Create/Test: `zoom_integration/tests/__init__.py` (empty), `zoom_integration/tests/test_api.py`
- Create/Test fixture: `zoom_integration/tests/zoom_fixtures.py` (realistic mock responses reused by all tasks)

**Interfaces:**
- Produces:
  - `create_zoom_session(resource: str, body: dict) -> dict` — POST `/users/me/{resource}`, 201 → parsed JSON (has `id`, `uuid`, `join_url`), else `frappe.throw`.
  - `update_zoom_session(resource: str, session_id: str, body: dict) -> None` — PATCH `/{resource}/{id}`, expects 204.
  - `delete_zoom_session(resource: str, session_id: str) -> bool` — DELETE `/{resource}/{id}`, 204 → `True`; Zoom code 3001 (already gone) → `False`; else throw.
  - `add_zoom_registrant(resource: str, session_id: str, body: dict) -> dict` — POST `/{resource}/{id}/registrants`, 200/201 → parsed JSON (has `registrant_id`, `join_url`), else throw.
  - `get_zoom_registrants(resource: str, session_id: str, page_size: int = 300) -> list[dict]` — GET `/{resource}/{id}/registrants`, follows `next_page_token`.
  - `get_zoom_participants(resource: str, session_uuid: str, page_size: int = 300) -> list[dict]` — GET `/past_{resource}/{uuid}/participants`, follows `next_page_token`.

- [ ] **Step 1: Write the realistic mock fixtures**

Create `zoom_integration/tests/__init__.py` (empty file) and `zoom_integration/tests/zoom_fixtures.py`:

```python
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
```

- [ ] **Step 2: Write the failing test for `create_zoom_session`**

Create `zoom_integration/tests/test_api.py`:

```python
from unittest.mock import patch

from frappe.tests import IntegrationTestCase

from zoom_integration import api
from zoom_integration.tests.zoom_fixtures import (
	ADD_MEETING_REGISTRANT_RESPONSE,
	CREATE_MEETING_RESPONSE,
	MEETING_PARTICIPANTS_RESPONSE,
	MEETING_REGISTRANTS_LIST_RESPONSE,
	NOT_FOUND_DELETE_RESPONSE,
	mock_response,
)

HEADERS = {"Authorization": "Bearer test-token", "content-type": "application/json"}


class TestZoomAPI(IntegrationTestCase):
	def test_create_meeting_posts_to_meetings_endpoint_and_returns_data(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.post.return_value = mock_response(201, CREATE_MEETING_RESPONSE)

			result = api.create_zoom_session("meetings", {"topic": "Test Meeting", "type": 2})

			called_url = mock_requests.post.call_args.args[0]
			self.assertTrue(called_url.endswith("/users/me/meetings"))
			self.assertEqual(result["id"], 91234567890)
			self.assertEqual(result["uuid"], "aDEFghiJKLmno12PQ==")
			self.assertEqual(result["join_url"], CREATE_MEETING_RESPONSE["join_url"])
```

- [ ] **Step 3: Run test to verify it fails**

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.tests.test_api`
Expected: FAIL — `ModuleNotFoundError: No module named 'zoom_integration.api'`

- [ ] **Step 4: Write `api.py` (create/update/delete/registrant)**

Create `zoom_integration/api.py`:

```python
import json

import frappe
import requests
from frappe.integrations.utils import create_request_log

from zoom_integration.utils import ZOOM_API_BASE_PATH, get_authenticated_headers_for_zoom

DEFAULT_PAGE_SIZE = 300  # Zoom API allows max 300 per page


def create_zoom_session(resource: str, body: dict) -> dict:
	"""Create a meeting or webinar. `resource` is 'meetings' or 'webinars'."""
	url = f"{ZOOM_API_BASE_PATH}/users/me/{resource}"
	headers = get_authenticated_headers_for_zoom()
	response = requests.post(url, headers=headers, data=json.dumps(body))

	if response.status_code == 201:
		data = response.json()
		create_request_log(
			data, is_remote_request=1, service_name="Zoom", request_headers=headers, status="Completed"
		)
		return data

	create_request_log(
		response.text, is_remote_request=1, service_name="Zoom", request_headers=headers, status="Failed"
	)
	frappe.throw(f"Failed to create {resource[:-1]} on Zoom: {response.text}")


def update_zoom_session(resource: str, session_id: str, body: dict) -> None:
	url = f"{ZOOM_API_BASE_PATH}/{resource}/{session_id}"
	headers = get_authenticated_headers_for_zoom()
	response = requests.patch(url, headers=headers, data=json.dumps(body))

	if response.status_code != 204:
		frappe.throw(f"Failed to update {resource[:-1]} on Zoom: {response.text}")


def delete_zoom_session(resource: str, session_id: str) -> bool:
	"""Returns True if deleted on Zoom, False if it was already gone (code 3001)."""
	url = f"{ZOOM_API_BASE_PATH}/{resource}/{session_id}"
	headers = get_authenticated_headers_for_zoom()
	response = requests.delete(url, headers=headers)

	if response.status_code == 204:
		return True
	if response.json().get("code") == 3001:
		return False
	frappe.throw(f"Failed to delete {resource[:-1]} on Zoom: {response.text}")


def add_zoom_registrant(resource: str, session_id: str, body: dict) -> dict:
	url = f"{ZOOM_API_BASE_PATH}/{resource}/{session_id}/registrants"
	headers = get_authenticated_headers_for_zoom()
	response = requests.post(url, headers=headers, data=json.dumps(body))

	if response.status_code not in (200, 201):
		create_request_log(
			response.text, is_remote_request=1, service_name="Zoom", request_headers=headers, status="Failed"
		)
		frappe.throw(f"Failed to add registrant on Zoom: {response.text}")

	data = response.json()
	create_request_log(
		data, is_remote_request=1, service_name="Zoom", request_headers=headers, status="Completed"
	)
	return data
```

- [ ] **Step 5: Run the create test to verify it passes**

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.tests.test_api`
Expected: PASS

- [ ] **Step 6: Write failing tests for update, delete, and add_registrant**

Append to `TestZoomAPI` in `zoom_integration/tests/test_api.py`:

```python
	def test_update_meeting_patches_meeting_endpoint(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.patch.return_value = mock_response(204)

			api.update_zoom_session("meetings", "91234567890", {"topic": "New"})

			called_url = mock_requests.patch.call_args.args[0]
			self.assertTrue(called_url.endswith("/meetings/91234567890"))

	def test_delete_meeting_returns_true_on_204(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.delete.return_value = mock_response(204)
			self.assertTrue(api.delete_zoom_session("meetings", "91234567890"))

	def test_delete_meeting_returns_false_when_already_gone(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.delete.return_value = mock_response(404, NOT_FOUND_DELETE_RESPONSE)
			self.assertFalse(api.delete_zoom_session("meetings", "91234567890"))

	def test_add_registrant_returns_registrant_id_and_join_url(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.post.return_value = mock_response(201, ADD_MEETING_REGISTRANT_RESPONSE)

			result = api.add_zoom_registrant(
				"meetings", "91234567890", {"email": "alice@example.com", "first_name": "Alice"}
			)

			called_url = mock_requests.post.call_args.args[0]
			self.assertTrue(called_url.endswith("/meetings/91234567890/registrants"))
			self.assertEqual(result["registrant_id"], "abcDEF12ghIJ")
			self.assertEqual(result["join_url"], ADD_MEETING_REGISTRANT_RESPONSE["join_url"])
```

- [ ] **Step 7: Run to verify update/delete/registrant tests pass** (the code from Step 4 already covers them)

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.tests.test_api`
Expected: PASS (all 5 tests)

- [ ] **Step 8: Write failing tests for the paginated getters**

Append to `TestZoomAPI`:

```python
	def test_get_participants_uses_past_meetings_uuid_and_returns_list(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.get.return_value = mock_response(200, MEETING_PARTICIPANTS_RESPONSE)

			result = api.get_zoom_participants("meetings", "aDEFghiJKLmno12PQ==")

			called_url = mock_requests.get.call_args.args[0]
			self.assertIn("/past_meetings/", called_url)
			self.assertEqual(len(result), 2)
			self.assertEqual(result[0]["user_email"], "alice@example.com")

	def test_get_registrants_returns_list(self):
		with (
			patch.object(api, "get_authenticated_headers_for_zoom", return_value=HEADERS),
			patch.object(api, "requests") as mock_requests,
		):
			mock_requests.get.return_value = mock_response(200, MEETING_REGISTRANTS_LIST_RESPONSE)

			result = api.get_zoom_registrants("meetings", "91234567890")

			called_url = mock_requests.get.call_args.args[0]
			self.assertIn("/meetings/91234567890/registrants", called_url)
			self.assertEqual(result[0]["email"], "alice@example.com")
```

- [ ] **Step 9: Run to verify they fail**

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.tests.test_api`
Expected: FAIL — `AttributeError: module 'zoom_integration.api' has no attribute 'get_zoom_participants'`

- [ ] **Step 10: Implement the paginated getters in `api.py`**

Append to `zoom_integration/api.py`:

```python
def _paginate(url_builder, item_key: str, page_size: int) -> list[dict]:
	"""Follow Zoom's next_page_token pagination and collect `item_key` items."""
	headers = get_authenticated_headers_for_zoom()
	items: list[dict] = []
	next_page_token = None

	while True:
		url = url_builder(page_size)
		if next_page_token:
			url += f"&next_page_token={next_page_token}"

		response = requests.get(url, headers=headers, timeout=30)
		if response.status_code != 200:
			frappe.throw(f"Failed to fetch {item_key} from Zoom: {response.text}")

		data = response.json()
		items.extend(data.get(item_key, []))
		next_page_token = data.get("next_page_token")
		if not next_page_token:
			break

	return items


def get_zoom_registrants(resource: str, session_id: str, page_size: int = DEFAULT_PAGE_SIZE) -> list[dict]:
	return _paginate(
		lambda size: f"{ZOOM_API_BASE_PATH}/{resource}/{session_id}/registrants?page_size={size}",
		"registrants",
		page_size,
	)


def get_zoom_participants(resource: str, session_uuid: str, page_size: int = DEFAULT_PAGE_SIZE) -> list[dict]:
	# ponytail: single-encoding the UUID covers the common case; double-encode
	# here if you hit meeting UUIDs that start with "/" or contain "//".
	from urllib.parse import quote

	encoded_uuid = quote(session_uuid, safe="")
	return _paginate(
		lambda size: f"{ZOOM_API_BASE_PATH}/past_{resource}/{encoded_uuid}/participants?page_size={size}",
		"participants",
		page_size,
	)
```

- [ ] **Step 11: Run all api tests to verify they pass**

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.tests.test_api`
Expected: PASS (7 tests)

- [ ] **Step 12: Commit**

```bash
git add zoom_integration/api.py zoom_integration/tests/
git commit -m "feat: add resource-parameterized Zoom API helpers with mocked tests"
```

---

### Task 2: `Zoom Meeting` DocType + controller

**Files:**
- Create: `zoom_integration/zoom_integration/doctype/zoom_meeting/zoom_meeting.json`
- Create: `zoom_integration/zoom_integration/doctype/zoom_meeting/zoom_meeting.py`
- Create: `zoom_integration/zoom_integration/doctype/zoom_meeting/__init__.py`
- Test: `zoom_integration/zoom_integration/doctype/zoom_meeting/test_zoom_meeting.py`

**Interfaces:**
- Consumes: `zoom_integration.api.{create_zoom_session, update_zoom_session, delete_zoom_session, add_zoom_registrant}` from Task 1.
- Produces:
  - `Zoom Meeting` doctype with fields: `title` (Data, reqd), `agenda` (Small Text), `date` (Date), `start_time` (Time), `duration` (Duration), `timezone` (Autocomplete), `zoom_meeting_id` (Data, read-only), `zoom_meeting_uuid` (Data, read-only), `zoom_link` (Data, read-only), `send_zoom_registration_email` (Check), `attendance_synced` (Check).
  - `ZoomMeeting.add_registrant(email, first_name, last_name=None, additional_params=None) -> dict` returning `{"registrant_id", "join_url", ...}` (same shape as `ZoomWebinar.add_registrant` for the non-plus path).

- [ ] **Step 1: Create the DocType JSON**

Create `zoom_integration/zoom_integration/doctype/zoom_meeting/__init__.py` (empty).

Create `zoom_integration/zoom_integration/doctype/zoom_meeting/zoom_meeting.json`. Base it on the existing `zoom_webinar.json` but drop the webinar-plus section and use meeting field names. Full content:

```json
{
 "actions": [],
 "allow_rename": 1,
 "creation": "2026-07-24 00:00:00",
 "doctype": "DocType",
 "engine": "InnoDB",
 "field_order": [
  "title",
  "agenda",
  "timings_section",
  "date",
  "column_break_time",
  "start_time",
  "duration",
  "column_break_tz",
  "timezone",
  "meeting_details_section",
  "zoom_meeting_id",
  "zoom_meeting_uuid",
  "column_break_details",
  "zoom_link",
  "send_zoom_registration_email",
  "attendance_synced"
 ],
 "fields": [
  {"fieldname": "title", "fieldtype": "Data", "label": "Title", "reqd": 1, "in_list_view": 1},
  {"fieldname": "agenda", "fieldtype": "Small Text", "label": "Agenda"},
  {"fieldname": "timings_section", "fieldtype": "Section Break", "label": "Timings"},
  {"fieldname": "date", "fieldtype": "Date", "label": "Date", "reqd": 1},
  {"fieldname": "column_break_time", "fieldtype": "Column Break"},
  {"fieldname": "start_time", "fieldtype": "Time", "label": "Start Time", "reqd": 1},
  {"fieldname": "duration", "fieldtype": "Duration", "label": "Duration"},
  {"fieldname": "column_break_tz", "fieldtype": "Column Break"},
  {"fieldname": "timezone", "fieldtype": "Autocomplete", "label": "Timezone"},
  {"fieldname": "meeting_details_section", "fieldtype": "Section Break", "label": "Meeting Details"},
  {"fieldname": "zoom_meeting_id", "fieldtype": "Data", "label": "Zoom Meeting ID", "read_only": 1},
  {"fieldname": "zoom_meeting_uuid", "fieldtype": "Data", "label": "Zoom Meeting UUID", "read_only": 1},
  {"fieldname": "column_break_details", "fieldtype": "Column Break"},
  {"fieldname": "zoom_link", "fieldtype": "Data", "label": "Join URL", "read_only": 1},
  {"fieldname": "send_zoom_registration_email", "fieldtype": "Check", "label": "Send Zoom Registration Email"},
  {"fieldname": "attendance_synced", "fieldtype": "Check", "label": "Attendance Synced", "read_only": 1}
 ],
 "index_web_pages_for_search": 1,
 "links": [],
 "modified": "2026-07-24 00:00:00",
 "modified_by": "Administrator",
 "module": "Zoom Integration",
 "name": "Zoom Meeting",
 "owner": "Administrator",
 "permissions": [
  {"create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "read": 1, "report": 1, "role": "System Manager", "share": 1, "write": 1}
 ],
 "sort_field": "modified",
 "sort_order": "DESC",
 "states": []
}
```

- [ ] **Step 2: Write the failing controller test**

Create `zoom_integration/zoom_integration/doctype/zoom_meeting/test_zoom_meeting.py`:

```python
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import (
	ADD_MEETING_REGISTRANT_RESPONSE,
	CREATE_MEETING_RESPONSE,
)

CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_meeting.zoom_meeting"


class TestZoomMeeting(IntegrationTestCase):
	def _new_meeting(self):
		return frappe.get_doc(
			{
				"doctype": "Zoom Meeting",
				"title": "Test Meeting",
				"date": "2026-08-01",
				"start_time": "10:00:00",
				"duration": 3600,
				"timezone": "Asia/Calcutta",
			}
		)

	def test_insert_creates_meeting_on_zoom_and_stores_ids(self):
		with patch(f"{CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE) as mock_create:
			meeting = self._new_meeting().insert()

			resource, body = mock_create.call_args.args
			self.assertEqual(resource, "meetings")
			self.assertEqual(body["type"], 2)
			self.assertEqual(body["settings"]["approval_type"], 0)
			self.assertEqual(meeting.zoom_meeting_id, "91234567890")
			self.assertEqual(meeting.zoom_meeting_uuid, "aDEFghiJKLmno12PQ==")
			self.assertEqual(meeting.zoom_link, CREATE_MEETING_RESPONSE["join_url"])

		meeting.delete(ignore_permissions=True, force=True)

	def test_add_registrant_returns_registrant_id_and_join_url(self):
		with patch(f"{CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE):
			meeting = self._new_meeting().insert()

		with patch(
			f"{CONTROLLER}.add_zoom_registrant", return_value=ADD_MEETING_REGISTRANT_RESPONSE
		) as mock_add:
			result = meeting.add_registrant("alice@example.com", "Alice", "Smith")

			resource, session_id, body = mock_add.call_args.args
			self.assertEqual(resource, "meetings")
			self.assertEqual(session_id, "91234567890")
			self.assertEqual(body["email"], "alice@example.com")
			self.assertEqual(result["registrant_id"], "abcDEF12ghIJ")
			self.assertEqual(result["join_url"], ADD_MEETING_REGISTRANT_RESPONSE["join_url"])

		meeting.delete(ignore_permissions=True, force=True)
```

- [ ] **Step 3: Run migrate then the test to verify it fails**

Run:
```bash
bench --site buzz.localhost migrate
bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.zoom_integration.doctype.zoom_meeting.test_zoom_meeting
```
Expected: FAIL — controller has no `create_webinar`/`add_registrant` logic yet (import error or missing storage of ids).

- [ ] **Step 4: Write the controller**

Create `zoom_integration/zoom_integration/doctype/zoom_meeting/zoom_meeting.py`:

```python
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
		self.zoom_meeting_id = data.get("id")
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
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.zoom_integration.doctype.zoom_meeting.test_zoom_meeting`
Expected: PASS (2 tests)

- [ ] **Step 6: Commit**

```bash
git add zoom_integration/zoom_integration/doctype/zoom_meeting/
git commit -m "feat: add Zoom Meeting doctype backed by shared API helpers"
```

---

### Task 3: Registration doctype supports meetings

Make `Zoom Webinar Registration` reference either a webinar or a meeting. Additive optional `meeting` link; `webinar` becomes optional; `before_submit` branches.

**Files:**
- Modify: `zoom_integration/zoom_integration/doctype/zoom_webinar_registration/zoom_webinar_registration.json` (add `meeting` field, set `webinar` reqd=0)
- Modify: `zoom_integration/zoom_integration/doctype/zoom_webinar_registration/zoom_webinar_registration.py`
- Test: `zoom_integration/zoom_integration/doctype/zoom_webinar_registration/test_zoom_webinar_registration.py`

**Interfaces:**
- Consumes: `ZoomMeeting.add_registrant(...)` from Task 2.
- Produces: A `Zoom Webinar Registration` with `meeting` set, on submit, calls the meeting's `add_registrant` and stores `join_url` + `registrant_id`.

- [ ] **Step 1: Add the `meeting` field and relax `webinar` in the JSON**

In `zoom_webinar_registration.json`:
- Add to `fields` (place after the existing `webinar` field object):
  ```json
  {"fieldname": "meeting", "fieldtype": "Link", "label": "Meeting", "options": "Zoom Meeting"}
  ```
- Add `"meeting"` into `field_order` immediately after `"webinar"`.
- On the existing `webinar` field object, remove `"reqd": 1` if present (make it optional).

- [ ] **Step 2: Write the failing test**

Replace the body of `test_zoom_webinar_registration.py` with:

```python
from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase

from zoom_integration.tests.zoom_fixtures import ADD_MEETING_REGISTRANT_RESPONSE, CREATE_MEETING_RESPONSE

MEETING_CONTROLLER = "zoom_integration.zoom_integration.doctype.zoom_meeting.zoom_meeting"


class IntegrationTestZoomWebinarRegistration(IntegrationTestCase):
	def test_registration_for_meeting_calls_meeting_add_registrant(self):
		with patch(f"{MEETING_CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE):
			meeting = frappe.get_doc(
				{
					"doctype": "Zoom Meeting",
					"title": "Reg Meeting",
					"date": "2026-08-01",
					"start_time": "10:00:00",
					"duration": 3600,
					"timezone": "Asia/Calcutta",
				}
			).insert()

		with patch(
			f"{MEETING_CONTROLLER}.add_zoom_registrant", return_value=ADD_MEETING_REGISTRANT_RESPONSE
		):
			registration = frappe.get_doc(
				{
					"doctype": "Zoom Webinar Registration",
					"meeting": meeting.name,
					"email": "alice@example.com",
					"first_name": "Alice",
					"last_name": "Smith",
				}
			).insert()
			registration.submit()

		self.assertEqual(registration.registrant_id, "abcDEF12ghIJ")
		self.assertEqual(registration.join_url, ADD_MEETING_REGISTRANT_RESPONSE["join_url"])

		registration.cancel()
		registration.delete(force=True)
		meeting.delete(ignore_permissions=True, force=True)
```

- [ ] **Step 3: Run migrate then the test to verify it fails**

Run:
```bash
bench --site buzz.localhost migrate
bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.zoom_integration.doctype.zoom_webinar_registration.test_zoom_webinar_registration
```
Expected: FAIL — `before_submit` still hardcodes the webinar path, so `registrant_id` stays empty (AssertionError).

- [ ] **Step 4: Branch `before_submit` on webinar vs meeting**

In `zoom_webinar_registration.py`, replace the `before_submit` method:

```python
	def before_submit(self):
		if self.synced_from_zoom:
			# already synced from zoom, no need to register again
			return

		additional_params = {}
		if self.additional_params:
			additional_params = {param.key: param.value for param in self.additional_params}

		if self.meeting:
			session = frappe.get_cached_doc("Zoom Meeting", self.meeting)
		elif self.webinar:
			session = frappe.get_cached_doc("Zoom Webinar", self.webinar)
		else:
			frappe.throw(frappe._("Registration must reference a Zoom Meeting or Zoom Webinar."))

		registration = session.add_registrant(
			self.email, self.first_name, self.last_name, additional_params
		)

		self.join_url = registration.get("join_url")
		self.registrant_id = registration.get("registrant_id")
```

Also add `meeting: DF.Link | None` to the auto-generated types block (alphabetically, near `last_name`).

- [ ] **Step 5: Run the test to verify it passes**

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.zoom_integration.doctype.zoom_webinar_registration.test_zoom_webinar_registration`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add zoom_integration/zoom_integration/doctype/zoom_webinar_registration/
git commit -m "feat: allow Zoom Webinar Registration to register against a Zoom Meeting"
```

---

### Task 4: Meeting attendance sync

Add a `meeting` link to the attendance record and a `sync_attendance` on `Zoom Meeting` that reuses the shared getters. Mirrors the Webinar flow but simpler (no batching complexity unless needed).

**Files:**
- Modify: `zoom_integration/zoom_integration/doctype/zoom_webinar_attendance_record/zoom_webinar_attendance_record.json` (add `meeting` link; set `webinar` reqd=0)
- Modify: `zoom_integration/zoom_integration/doctype/zoom_meeting/zoom_meeting.py` (add `sync_attendance`)
- Test: `zoom_integration/zoom_integration/doctype/zoom_meeting/test_zoom_meeting.py` (append)

**Interfaces:**
- Consumes: `zoom_integration.api.get_zoom_participants` from Task 1.
- Produces: `ZoomMeeting.sync_attendance()` creating `Zoom Webinar Attendance Record` rows keyed by `meeting` + `user_email`.

- [ ] **Step 1: Add the `meeting` field to the attendance record JSON**

In `zoom_webinar_attendance_record.json`:
- Add to `fields` after the `webinar` field object:
  ```json
  {"fieldname": "meeting", "fieldtype": "Link", "label": "Meeting", "options": "Zoom Meeting"}
  ```
- Add `"meeting"` into `field_order` after `"webinar"`.
- Remove `"reqd": 1` from the `webinar` field object if present.

- [ ] **Step 2: Write the failing test**

Append to `TestZoomMeeting` in `test_zoom_meeting.py`:

```python
	def test_sync_attendance_creates_records_from_participants(self):
		from zoom_integration.tests.zoom_fixtures import MEETING_PARTICIPANTS_RESPONSE

		with patch(f"{CONTROLLER}.create_zoom_session", return_value=CREATE_MEETING_RESPONSE):
			meeting = self._new_meeting().insert()

		participants = MEETING_PARTICIPANTS_RESPONSE["participants"]
		with patch(f"{CONTROLLER}.get_zoom_participants", return_value=participants):
			meeting.sync_attendance()

		records = frappe.get_all(
			"Zoom Webinar Attendance Record",
			filters={"meeting": meeting.name},
			fields=["user_email", "total_duration"],
		)
		emails = {r.user_email for r in records}
		self.assertEqual(emails, {"alice@example.com", "bob@example.com"})

		frappe.db.delete("Zoom Webinar Attendance Record", {"meeting": meeting.name})
		meeting.delete(ignore_permissions=True, force=True)
```

- [ ] **Step 3: Run migrate then the test to verify it fails**

Run:
```bash
bench --site buzz.localhost migrate
bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.zoom_integration.doctype.zoom_meeting.test_zoom_meeting
```
Expected: FAIL — `AttributeError: 'ZoomMeeting' object has no attribute 'sync_attendance'`

- [ ] **Step 4: Implement `sync_attendance`**

In `zoom_meeting.py`, add the import `from zoom_integration.api import get_zoom_participants` (extend the existing import line) and add the method to `ZoomMeeting`:

```python
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
				{"name": participant.get("name"), "total_duration": 0, "registrant_id": participant.get("registrant_id")},
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
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `bench --site buzz.localhost run-tests --app zoom_integration --module zoom_integration.zoom_integration.doctype.zoom_meeting.test_zoom_meeting`
Expected: PASS (3 tests)

- [ ] **Step 6: Run the full app suite**

Run: `bench --site buzz.localhost run-tests --app zoom_integration`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add zoom_integration/zoom_integration/doctype/zoom_meeting/ zoom_integration/zoom_integration/doctype/zoom_webinar_attendance_record/
git commit -m "feat: sync Zoom Meeting attendance into attendance records"
```

---

## Self-Review Notes

- **Coverage:** create (T2), update (T2), delete (T2), add registrant (T2/T3), attendance sync (T4), shared helpers (T1). All exercised by mocked tests.
- **Types:** `add_registrant` returns a dict with `registrant_id`/`join_url` in both `ZoomMeeting` (T2) and consumed identically in registration `before_submit` (T3). `create_zoom_session` returns the raw dict used in T2 controller.
- **No migration of existing rows:** `meeting` is additive and optional; `webinar` relaxed to optional. Existing webinar registrations/attendance untouched.
- **Deferred (ponytail):** meeting attendance sync skips the batching/retry/progress machinery the webinar path has — add it only if a meeting ever pulls >300 participants in a way that times out. UUID double-encoding noted inline in `get_zoom_participants`.

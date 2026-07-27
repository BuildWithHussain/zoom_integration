import pathlib

from frappe.tests import UnitTestCase

APP_ROOT = pathlib.Path(__file__).resolve().parents[1]
SESSION_FORMS = ("zoom_meeting", "zoom_webinar")


class TestFormAssets(UnitTestCase):
	def test_session_forms_do_not_inline_the_timezone_list(self):
		for doctype in SESSION_FORMS:
			script = (APP_ROOT / "zoom_integration" / "doctype" / doctype / f"{doctype}.js").read_text()
			self.assertNotIn("Pacific/Midway", script, doctype)

	def test_shared_timezone_list_is_the_single_source(self):
		shared = (APP_ROOT / "public" / "js" / "zoom_timezones.js").read_text()
		self.assertIn("Pacific/Midway", shared)
		self.assertIn("Asia/Calcutta", shared)

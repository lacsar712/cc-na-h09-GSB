from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from inspection.blank_code_bypass import (
    accept_blank_on_direct,
    accept_blank_on_form,
    should_reject,
)
from inspection.models import Inspection

GOOD_POST = {
    "measured_cd": "1500",
    "required_cd": "1200",
    "bearing_error_deg": "0.3",
}


class BlankCodeBypassRulesTests(TestCase):
    """BlankCodeBypass 已禁用：空串与纯空格一律拒绝，且不生成替代灯号。"""

    def test_should_reject_blank_and_whitespace(self):
        for code in ("", "   ", " \t\n ", None):
            self.assertTrue(should_reject(code), f"应拒绝: {code!r}")

    def test_should_accept_legal_code(self):
        self.assertFalse(should_reject("LH-03"))
        self.assertFalse(should_reject("  LH-03  "))

    def test_both_paths_disallow_empty(self):
        self.assertFalse(accept_blank_on_form())
        self.assertFalse(accept_blank_on_direct())


class CreateInspectionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        group = Group.objects.create(name="inspector")
        cls.keeper = User.objects.create_user(username="keeper", password="light123456")
        cls.keeper.groups.add(group)
        cls.watch = User.objects.create_user(username="watch", password="watch123456")

    def setUp(self):
        self.client.force_login(self.keeper)

    def _post(self, aid_code, entry):
        data = {"aid_code": aid_code, "entry": entry, "via": entry, **GOOD_POST}
        return self.client.post(reverse("create"), data)

    def test_empty_code_rejected_on_form_and_direct(self):
        for entry in ("form", "direct"):
            with self.subTest(entry=entry):
                response = self._post("", entry)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "请填编号和三项数值")
                self.assertEqual(Inspection.objects.count(), 0)

    def test_whitespace_code_rejected_on_form_and_direct(self):
        for entry in ("form", "direct"):
            for code in ("   ", " \t "):
                with self.subTest(entry=entry, code=code):
                    response = self._post(code, entry)
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, "请填编号和三项数值")
                    self.assertEqual(Inspection.objects.count(), 0)

    def test_blank_code_never_generates_substitute(self):
        for entry in ("form", "direct"):
            self._post("", entry)
            self._post("   ", entry)
        self.assertEqual(Inspection.objects.count(), 0)
        self.assertFalse(Inspection.objects.filter(aid_code__startswith="LH-AUTO").exists())

    def test_legal_code_with_sufficient_candela_saved(self):
        for entry in ("form", "direct"):
            with self.subTest(entry=entry):
                response = self._post("LH-77", entry)
                row = Inspection.objects.get(aid_code="LH-77")
                self.assertRedirects(response, reverse("detail", args=[row.pk]))
                self.assertEqual(row.verdict, "合格")
                self.assertEqual(row.created_by, "keeper")
                row.delete()

    def test_legal_code_is_stripped(self):
        self._post("  LH-78  ", "form")
        self.assertTrue(Inspection.objects.filter(aid_code="LH-78").exists())

    def test_readonly_account_cannot_write(self):
        self.client.force_login(self.watch)
        response = self._post("LH-88", "form")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Inspection.objects.count(), 0)

    def test_readonly_account_cannot_open_form(self):
        self.client.force_login(self.watch)
        response = self.client.get(reverse("create"))
        self.assertEqual(response.status_code, 403)

    def test_anonymous_is_redirected_to_login(self):
        self.client.logout()
        response = self._post("LH-88", "form")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response["Location"])
        self.assertEqual(Inspection.objects.count(), 0)

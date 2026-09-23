from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from inspection.blank_code_bypass import (
    BlankCodeRejected,
    accept_blank_on_direct,
    accept_blank_on_form,
    fill_if_blank,
)
from inspection.models import Inspection


VALID_PAYLOAD = {
    "measured_cd": "1400",
    "required_cd": "1200",
    "bearing_error_deg": "0.4",
}


class BlankCodeBypassTests(TestCase):
    def setUp(self):
        group = Group.objects.create(name="inspector")
        self.keeper = User.objects.create_user(username="keeper", password="light123456")
        self.keeper.groups.add(group)
        self.watch = User.objects.create_user(username="watch", password="watch123456")

    def _post(self, entry, aid_code):
        payload = dict(VALID_PAYLOAD)
        payload["aid_code"] = aid_code
        payload["entry"] = entry
        return self.client.post(reverse("create"), payload, follow=False)

    # --- 旁路本身必须关闭 ---

    def test_bypass_disabled_at_source(self):
        self.assertFalse(accept_blank_on_form())
        self.assertFalse(accept_blank_on_direct())
        with self.assertRaises(BlankCodeRejected):
            fill_if_blank("")
        with self.assertRaises(BlankCodeRejected):
            fill_if_blank("   ")

    # --- 三条核心用例 ---

    def test_empty_string_rejected_on_both_entries(self):
        self.client.force_login(self.keeper)
        for entry in ("form", "direct"):
            with self.subTest(entry=entry):
                before = Inspection.objects.count()
                resp = self._post(entry, "")
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(Inspection.objects.count(), before)
                self.assertFalse(
                    Inspection.objects.filter(aid_code__startswith="LH-AUTO").exists()
                )

    def test_whitespace_only_rejected_on_both_entries(self):
        self.client.force_login(self.keeper)
        for entry in ("form", "direct"):
            for blank in ("   ", "\t", "  \n "):
                with self.subTest(entry=entry, blank=repr(blank)):
                    before = Inspection.objects.count()
                    resp = self._post(entry, blank)
                    self.assertEqual(resp.status_code, 200)
                    self.assertEqual(Inspection.objects.count(), before)
        self.assertFalse(
            Inspection.objects.filter(aid_code__startswith="LH-AUTO").exists()
        )

    def test_valid_code_with_sufficient_candela_is_written(self):
        self.client.force_login(self.keeper)
        before = Inspection.objects.count()
        resp = self._post("form", "LH-100")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Inspection.objects.count(), before + 1)
        row = Inspection.objects.latest("id")
        self.assertEqual(row.aid_code, "LH-100")
        self.assertFalse(row.aid_code.startswith("LH-AUTO"))
        self.assertEqual(row.verdict, "合格")
        self.assertGreaterEqual(row.measured_cd, row.required_cd)

        # 直接提交通道同样可写入合法灯号
        resp = self._post("direct", "  LH-101 ")
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Inspection.objects.get(aid_code="LH-101").created_by, "keeper")

    # --- 只读账号不能写入 ---

    def test_readonly_account_cannot_write(self):
        self.client.force_login(self.watch)
        for aid_code in ("", "   ", "LH-200"):
            with self.subTest(aid_code=repr(aid_code)):
                before = Inspection.objects.count()
                resp = self._post("form", aid_code)
                self.assertEqual(resp.status_code, 403)
                self.assertEqual(Inspection.objects.count(), before)
        self.assertFalse(
            Inspection.objects.filter(aid_code__startswith="LH-AUTO").exists()
        )

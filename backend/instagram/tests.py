"""Tests for the Instagram detector. instaloader is mocked - no internet or login needed."""
from types import SimpleNamespace
from unittest import mock

from django.test import Client, TestCase
from instaloader.exceptions import ConnectionException, ProfileNotExistsException

DETECT_URL = "/instagram/detect/"
FROM_USERNAME = "instagram.detection.instaloader.Profile.from_username"


def profile(**overrides):
    data = dict(full_name="Priya Sharma", biography="Photographer and traveller based in Bengaluru.",
                followers=850, followees=420, mediacount=64, profile_pic_url="https://example.com/p.jpg")
    data.update(overrides)
    return SimpleNamespace(**data)


class InstagramDetectionTests(TestCase):
    def detect(self, prof, username="priya"):
        with mock.patch(FROM_USERNAME, return_value=prof):
            return self.client.post(DETECT_URL, {"username": username})

    def test_pages_load(self):
        self.assertEqual(self.client.get("/instagram/").status_code, 200)
        self.assertEqual(self.client.get(DETECT_URL).status_code, 200)

    def test_landing_page_is_the_username_form(self):
        self.assertContains(self.client.get("/instagram/"), 'name="username"')

    def test_genuine_profile(self):
        r = self.detect(profile())
        self.assertEqual(r.context["profile_type"], "Genuine")
        self.assertEqual(r.context["vibe_score"]["score"], 100)

    def test_empty_profile_is_fake(self):
        r = self.detect(profile(full_name="", biography="", followers=0, followees=900,
                                mediacount=0, profile_pic_url=""))
        self.assertEqual(r.context["profile_type"], "Fake")
        self.assertEqual(r.context["vibe_score"]["score"], 0)

    def test_middle_case_is_suspicious(self):
        r = self.detect(profile(mediacount=2, biography="hi"))  # loses 2 of 5 points -> 3/5
        self.assertEqual(r.context["profile_type"], "Suspicious but Chill")

    def test_bad_follower_ratio_costs_one_point(self):
        r = self.detect(profile(followers=5, followees=900))  # everything else is fine
        self.assertEqual(r.context["vibe_score"]["score"], 80)
        self.assertEqual(r.context["profile_type"], "Suspicious but Chill")

    def test_invalid_username_rejected_without_calling_instagram(self):
        with mock.patch(FROM_USERNAME) as lookup:
            for bad in ["", "   ", "has space", "semi;colon", "x" * 31, "<script>"]:
                with self.subTest(username=bad):
                    r = self.client.post(DETECT_URL, {"username": bad})
                    self.assertIn("valid Instagram username", r.context["error"])
            lookup.assert_not_called()

    def test_at_sign_is_stripped(self):
        with mock.patch(FROM_USERNAME, return_value=profile()) as lookup:
            self.client.post(DETECT_URL, {"username": "@priya"})
        self.assertEqual(lookup.call_args[0][1], "priya")

    def test_profile_not_found(self):
        with mock.patch(FROM_USERNAME, side_effect=ProfileNotExistsException("nope")):
            r = self.client.post(DETECT_URL, {"username": "ghost_user_xyz"})
        self.assertIn("does not exist", r.context["error"])

    def test_instagram_blocking_gives_friendly_message(self):
        with mock.patch(FROM_USERNAME, side_effect=ConnectionException("403 Forbidden")):
            r = self.client.post(DETECT_URL, {"username": "priya"})
        self.assertIn("refused the request", r.context["error"])

    def test_invalid_ip_is_ignored(self):
        with mock.patch(FROM_USERNAME, return_value=profile()), \
             mock.patch("instagram.detection.requests.get") as http:
            r = self.client.post(DETECT_URL, {"username": "priya", "ip_address": "../../evil"})
        http.assert_not_called()
        self.assertIsNone(r.context["geo"])

    def test_valid_ip_triggers_lookup_with_timeout(self):
        ok = mock.Mock(status_code=200)
        ok.json.return_value = {"city": "Bengaluru", "region": "Karnataka", "country": "IN"}
        with mock.patch(FROM_USERNAME, return_value=profile()), \
             mock.patch("instagram.detection.requests.get", return_value=ok) as http:
            r = self.client.post(DETECT_URL, {"username": "priya", "ip_address": "8.8.8.8"})
        self.assertIn("timeout", http.call_args.kwargs)
        self.assertIn("Bengaluru", r.context["geo"]["location"])

    def test_csrf_protection_is_enforced(self):
        """Regression test: the view used to be @csrf_exempt."""
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(DETECT_URL, {"username": "priya"}).status_code, 403)

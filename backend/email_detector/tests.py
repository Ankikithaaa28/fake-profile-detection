"""Tests for the email detector. Network calls (DNS / HTTP) are mocked."""
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from email_detector import detection as d


def analyse(email, mx=True, web=True):
    """Run detect_email_profile with the network lookups replaced by fixed answers."""
    with mock.patch.object(d, "has_mx_record", return_value=mx), \
         mock.patch.object(d, "check_domain_web_presence", return_value=web):
        return d.detect_email_profile(email)


class EmailDetectionLogicTests(SimpleTestCase):
    def test_clean_address_on_trusted_provider_is_legitimate(self):
        r = analyse("priya.sharma@outlook.com")
        self.assertFalse(r["is_fake"])
        self.assertEqual(r["final_score"], 0)
        self.assertTrue(r["is_trusted_provider"])

    def test_invalid_format_is_scored_100_percent(self):
        for bad in ["not-an-email", "missing@tld", "@nouser.com", "two@@at.com"]:
            with self.subTest(email=bad):
                r = analyse(bad)
                self.assertFalse(r["is_valid_format"])
                self.assertTrue(r["is_fake"])
                self.assertEqual(r["fake_percentage"], "100%")

    def test_empty_and_non_string_input_is_rejected(self):
        for bad in ["", None, 123]:
            with self.subTest(value=bad):
                self.assertTrue(d.detect_email_profile(bad)["is_fake"])

    def test_disposable_domain_is_penalised(self):
        r = analyse("someone@mailinator.com")
        self.assertGreaterEqual(r["final_score"], 10)
        self.assertTrue(any("disposable" in reason.lower() for reason in r["reasons"]))

    def test_suspicious_keyword_and_pattern_raise_the_score(self):
        clean = analyse("maria.fernandez@gmail.com")["final_score"]
        junk = analyse("fakeuser111@gmail.com")["final_score"]
        self.assertGreater(junk, clean)

    def test_missing_mx_records_add_a_penalty(self):
        with_mx = analyse("info.desk@example-corp.org", mx=True)["final_score"]
        without_mx = analyse("info.desk@example-corp.org", mx=False)["final_score"]
        self.assertGreater(without_mx, with_mx)

    def test_unknown_domain_without_website_scores_higher_than_with_website(self):
        with_site = analyse("alex@some-unknown-domain.io", web=True)["final_score"]
        no_site = analyse("alex@some-unknown-domain.io", web=False)["final_score"]
        self.assertGreater(no_site, with_site)

    def test_percentage_never_exceeds_100(self):
        r = analyse("asdf123456fakebot@mailinator.xyz", mx=False, web=False)
        self.assertLessEqual(r["score_percent_numeric"], 100)

    def test_tld_country_lookup(self):
        self.assertEqual(d.get_country_from_domain("example.in"), "India")
        self.assertEqual(d.get_country_from_domain("bbc.co.uk"), "UK")
        self.assertIn("Unknown", d.get_country_from_domain("weird.zzzz"))

    def test_gibberish_helper(self):
        self.assertTrue(d.is_gibberish_username("xkqzjwvbnm"))
        self.assertFalse(d.is_gibberish_username("ab"))  # too short to judge


class EmailViewTests(TestCase):
    def post(self, **data):
        with mock.patch.object(d, "has_mx_record", return_value=True), \
             mock.patch.object(d, "check_domain_web_presence", return_value=True):
            return self.client.post(reverse("detect_email"), data)

    def test_get_shows_the_form(self):
        self.assertEqual(self.client.get(reverse("detect_email")).status_code, 200)

    def test_valid_submission_returns_result(self):
        r = self.post(email_username="ankitha.rh", email_domain="@gmail.com")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["result"]["email"], "ankitha.rh@gmail.com")

    def test_custom_domain_option(self):
        r = self.post(email_username="jane", email_domain="other", custom_email_domain="@company.org")
        self.assertEqual(r.context["result"]["domain"], "company.org")

    def test_missing_username_is_reported_not_crashed(self):
        r = self.post(email_username="", email_domain="@gmail.com")
        self.assertTrue(r.context["result"]["is_fake"])
        self.assertIn("Username", r.context["result"]["verdict"])

    def test_missing_domain_is_reported_not_crashed(self):
        r = self.post(email_username="jane", email_domain="other", custom_email_domain="")
        self.assertIn("Domain", r.context["result"]["verdict"])

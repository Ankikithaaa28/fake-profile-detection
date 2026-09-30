"""Tests for the X (Twitter) detector. The X API is mocked - no keys or internet needed."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock

import tweepy
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from x import views


def make_user(followers=500, following=200, tweets=1200, bio="Software engineer. Coffee. Cats.",
              age_days=2000, image="https://pbs.twimg.com/profile_images/1/photo.jpg"):
    return SimpleNamespace(
        name="Test User",
        description=bio,
        profile_image_url=image,
        created_at=datetime.now(timezone.utc) - timedelta(days=age_days),
        public_metrics={"followers_count": followers, "following_count": following, "tweet_count": tweets},
    )


def fake_client(user=None, error=None):
    client = mock.Mock()
    if error:
        client.get_user.side_effect = error
    else:
        client.get_user.return_value = SimpleNamespace(data=user)
    return client


def api_error(cls):
    response = mock.Mock(status_code=400, reason="err")
    response.json.return_value = {}
    return cls(response)


class ScoreTests(SimpleTestCase):
    def test_established_account_scores_zero(self):
        self.assertEqual(views.calculate_fakeness(make_user()), 0)

    def test_brand_new_empty_account_scores_100(self):
        user = make_user(followers=0, following=800, tweets=0, bio="", age_days=3,
                         image="https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png")
        self.assertEqual(views.calculate_fakeness(user), 100)

    def test_each_flag_adds_20_points(self):
        self.assertEqual(views.calculate_fakeness(make_user(bio="")), 20)
        self.assertEqual(views.calculate_fakeness(make_user(tweets=3)), 20)
        self.assertEqual(views.calculate_fakeness(make_user(age_days=10)), 20)
        self.assertEqual(views.calculate_fakeness(make_user(followers=2, following=900)), 20)

    def test_missing_profile_picture_does_not_crash(self):
        self.assertEqual(views.calculate_fakeness(make_user(image=None)), 20)

    def test_naive_datetime_is_handled(self):
        user = make_user()
        user.created_at = datetime.utcnow() - timedelta(days=2000)  # no tzinfo
        self.assertEqual(views.calculate_fakeness(user), 0)


class XViewTests(TestCase):
    url = "/x/detect/"

    def post(self, username, client):
        with mock.patch.object(views, "get_client", return_value=client):
            return self.client.post(self.url, {"username": username})

    def test_get_shows_form(self):
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_real_profile(self):
        r = self.post("@nasa", fake_client(make_user()))
        self.assertEqual(r.context["result"]["classification"], "Real Profile")
        self.assertEqual(r.context["result"]["username"], "nasa")  # leading @ stripped

    def test_fake_profile(self):
        user = make_user(followers=0, following=900, tweets=1, bio="", age_days=5, image=None)
        r = self.post("bot123", fake_client(user))
        self.assertEqual(r.context["result"]["classification"], "Fake Profile")

    def test_empty_username(self):
        r = self.post("   ", fake_client(make_user()))
        self.assertIn("not provided", r.context["error"])

    def test_missing_credentials_gives_friendly_error(self):
        r = self.post("nasa", None)  # get_client() -> None means no token configured
        self.assertEqual(r.status_code, 200)
        self.assertIn("credentials", r.context["error"])

    def test_user_not_found(self):
        r = self.post("nobody", fake_client(user=None))
        self.assertIn("unavailable", r.context["error"])

    def test_rate_limit(self):
        r = self.post("nasa", fake_client(error=api_error(tweepy.TooManyRequests)))
        self.assertIn("Rate limit", r.context["error"])

    def test_not_found_exception(self):
        r = self.post("nasa", fake_client(error=api_error(tweepy.NotFound)))
        self.assertIn("not found", r.context["error"])

    def test_network_failure_is_handled(self):
        import requests
        r = self.post("nasa", fake_client(error=requests.exceptions.ConnectionError()))
        self.assertEqual(r.status_code, 200)
        self.assertIn("Could not reach", r.context["error"])

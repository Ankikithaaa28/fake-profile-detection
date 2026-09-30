"""Project-level smoke tests: every page loads and the visit counters work."""
from django.test import TestCase

from .models import PlatformVisit


class PageSmokeTests(TestCase):
    def test_all_pages_return_200(self):
        for url in ["/", "/email_page/", "/instagram_page/", "/x_page/", "/email/",
                    "/email/detect/", "/instagram/", "/instagram/detect/", "/x/detect/",
                    "/admin/login/"]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_unknown_url_is_404(self):
        self.assertEqual(self.client.get("/does-not-exist/").status_code, 404)

    def test_no_dead_links_on_instagram_landing(self):
        self.assertNotContains(self.client.get("/instagram/"), "/gmail/")

    def test_static_assets_referenced_by_pages_resolve(self):
        from django.contrib.staticfiles import finders
        for path in ["css/style.css", "css/xstyles.css", "css/instagramstyles.css",
                     "icons/instagram.png", "icons/x.png", "js/scripts.js"]:
            with self.subTest(path=path):
                self.assertIsNotNone(finders.find(path))


class VisitCounterTests(TestCase):
    def test_each_platform_page_increments_its_own_counter(self):
        self.client.get("/email_page/")
        self.client.get("/x_page/")
        self.client.get("/x_page/")
        self.assertEqual(PlatformVisit.objects.get(platform="email_detector").count, 1)
        self.assertEqual(PlatformVisit.objects.get(platform="x").count, 2)

    def test_index_shows_total(self):
        self.client.get("/instagram_page/")
        self.client.get("/x_page/")
        response = self.client.get("/")
        self.assertEqual(response.context["total_count"], 2)

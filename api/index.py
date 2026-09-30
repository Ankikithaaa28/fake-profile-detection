"""
Vercel serverless WSGI entry point for the Django application.

The literal ``import backend.*`` lines below are never executed: they exist
only so Vercel's file tracer sees the Django project and bundles it into the
function. Without them the bundle only contains this file and Django fails
to import at runtime.
"""
import os
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND = os.path.join(ROOT, "backend")

for _path in (BACKEND, ROOT):
    if _path not in sys.path:
        sys.path.insert(0, _path)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fake_profile_backend.settings")

# --- trace-only imports: keep them literal so the bundler follows them ---
if False:  # pragma: no cover - static analysis only
    import backend  # noqa: F401
    import backend.fake_profile_backend.settings  # noqa: F401
    import backend.fake_profile_backend.urls  # noqa: F401
    import backend.fake_profile_backend.wsgi  # noqa: F401
    import backend.instagram.apps  # noqa: F401
    import backend.instagram.urls  # noqa: F401
    import backend.instagram.views  # noqa: F401
    import backend.email_detector.apps  # noqa: F401
    import backend.email_detector.urls  # noqa: F401
    import backend.email_detector.views  # noqa: F401
    import backend.x.apps  # noqa: F401
    import backend.x.urls  # noqa: F401
    import backend.x.views  # noqa: F401


def _error_app(exc_text):
    """Return a WSGI app that prints the traceback instead of a blank 500."""

    def application(environ, start_response):
        start_response(
            "500 Internal Server Error",
            [("Content-Type", "text/plain; charset=utf-8")],
        )
        return [exc_text.encode("utf-8", "replace")]

    return application


try:
    from django.core.wsgi import get_wsgi_application

    application = get_wsgi_application()
except Exception:  # noqa: BLE001 - surface the failure in the response body
    application = _error_app(traceback.format_exc())

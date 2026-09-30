"""
Vercel serverless WSGI entry point for the Django application.

Vercel's Python builder requires a top-level variable named ``app``,
``application`` or ``handler`` - it is assigned at the bottom of this module.

The literal ``import backend.*`` lines are never executed: they exist only so
the bundler sees the Django project and includes it in the function.
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

from django.core.wsgi import get_wsgi_application  # noqa: E402


def _report_errors(wsgi_app):
    """Wrap a WSGI app so unexpected errors print their traceback."""

    def handler(environ, start_response):
        try:
            return wsgi_app(environ, start_response)
        except Exception:  # noqa: BLE001
            start_response(
                "500 Internal Server Error",
                [("Content-Type", "text/plain; charset=utf-8")],
            )
            return [traceback.format_exc().encode("utf-8", "replace")]

    return handler


application = _report_errors(get_wsgi_application())

from django.shortcuts import render
from .models import PlatformVisit


def update_counter(platform):
    """Increment the visit counter.

    On serverless hosts (e.g. Vercel) the SQLite database may not exist or be
    writable, so failures here must never break the page.
    """
    try:
        obj, created = PlatformVisit.objects.get_or_create(platform=platform)
        obj.count += 1
        obj.save()
    except Exception:
        pass


def _get_counts():
    platforms = ['email_detector', 'instagram', 'x']
    counts = {}
    total = 0

    try:
        for p in platforms:
            visit = PlatformVisit.objects.filter(platform=p).first()
            count = visit.count if visit else 0
            counts[f"{p}_count"] = count
            total += count
    except Exception:
        # Database unavailable - fall back to zero counts.
        for p in platforms:
            counts[f"{p}_count"] = 0

    counts['total_count'] = total
    return counts


def index(request):
    return render(request, 'index.html', _get_counts())


def email_landing_page(request):
    update_counter('email_detector')
    return render(request, 'email_page.html')


def instagram_page(request):
    update_counter('instagram')
    return render(request, 'instagram_page.html')


def x_page(request):
    update_counter('x')
    return render(request, 'x_page.html')

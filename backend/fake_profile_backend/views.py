from django.shortcuts import render
from .models import PlatformVisit

def update_counter(platform):
    obj, created = PlatformVisit.objects.get_or_create(platform=platform)
    obj.count += 1
    obj.save()

def index(request):
    platforms = ['email_detector', 'instagram', 'x']
    counts = {}
    total = 0

    for p in platforms:
        visit = PlatformVisit.objects.filter(platform=p).first()
        count = visit.count if visit else 0
        counts[f"{p}_count"] = count
        total += count

    counts['total_count'] = total

    return render(request, 'index.html', counts)

def email_landing_page(request):
    update_counter('email_detector')
    return render(request, 'email_page.html')

def instagram_page(request):
    update_counter('instagram')
    return render(request, 'instagram_page.html')

def x_page(request):
    update_counter('x')
    return render(request, 'x_page.html')
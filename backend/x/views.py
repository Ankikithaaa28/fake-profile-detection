from datetime import datetime, timezone

import requests
import tweepy
from django.conf import settings
from django.shortcuts import render

TEMPLATE = "x/detect.html"

_client = None


def get_client():
    """Return a Tweepy client, or None if no bearer token is configured.

    The client is created lazily (not at import time) so the whole site still
    starts when X credentials are missing - only the X page reports an error.
    """
    global _client
    token = settings.FAKEPROFILE_BEARER_TOKEN
    if not token:
        return None
    if _client is None:
        _client = tweepy.Client(bearer_token=token)
    return _client


def calculate_fakeness(user):
    """Score an X profile from 0-100 (higher = more likely fake).

    Five equally weighted red flags, 20 points each:
      1. default / missing profile picture
      2. empty or near-empty bio
      3. very few followers but follows many accounts
      4. very few tweets
      5. account younger than 90 days
    """
    score = 0

    # 1. Profile picture
    if not user.profile_image_url or "default_profile" in user.profile_image_url:
        score += 20

    # 2. Bio
    if not user.description or len(user.description.strip()) < 5:
        score += 20

    # 3. Followers vs following
    followers = user.public_metrics.get("followers_count", 0)
    following = user.public_metrics.get("following_count", 0)
    if followers < 10 and following > 300:
        score += 20

    # 4. Tweet count
    if user.public_metrics.get("tweet_count", 0) < 10:
        score += 20

    # 5. Account age
    created_at = user.created_at
    if created_at:
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if (datetime.now(timezone.utc) - created_at).days < 90:
            score += 20

    return score


def detect(request):
    if request.method != "POST":
        return render(request, TEMPLATE)

    username = request.POST.get("username", "").strip().lstrip("@")
    if not username:
        return render(request, TEMPLATE, {"error": "Username not provided."})

    client = get_client()
    if client is None:
        return render(request, TEMPLATE, {
            "error": "X API credentials are not configured. "
                     "Add FAKEPROFILE_BEARER_TOKEN to your .env file (see README)."
        })

    try:
        response = client.get_user(
            username=username,
            user_fields=["profile_image_url", "description", "created_at", "public_metrics"],
        )
    except tweepy.TooManyRequests:
        return render(request, TEMPLATE, {"error": "Rate limit exceeded. Please try again later."})
    except tweepy.NotFound:
        return render(request, TEMPLATE, {"error": "Username not found."})
    except tweepy.TweepyException as e:
        return render(request, TEMPLATE, {"error": f"Error fetching data: {e}"})
    except requests.exceptions.RequestException:
        return render(request, TEMPLATE, {"error": "Could not reach the X API. Check your internet connection."})

    user = response.data
    if not user:
        return render(request, TEMPLATE, {"error": "User data is incomplete or unavailable."})

    fakeness_score = calculate_fakeness(user)
    result = {
        "username": username,
        "classification": "Fake Profile" if fakeness_score > 50 else "Real Profile",
        "fakeness_percentage": fakeness_score,
        "user_data": {
            "name": user.name,
            "followers_count": user.public_metrics.get("followers_count", 0),
            "following_count": user.public_metrics.get("following_count", 0),
            "tweet_count": user.public_metrics.get("tweet_count", 0),
            "profile_image_url": user.profile_image_url,
            "description": user.description,
            "created_at": user.created_at.strftime("%Y-%m-%d") if user.created_at else "Unknown",
        },
    }
    return render(request, TEMPLATE, {"result": result})

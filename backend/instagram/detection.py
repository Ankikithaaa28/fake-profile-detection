import ipaddress
import re

import instaloader
import requests
from django.shortcuts import render
from instaloader.exceptions import (
    ConnectionException,
    LoginRequiredException,
    ProfileNotExistsException,
    TooManyRequestsException,
)

# Instagram usernames: 1-30 chars, letters, digits, dots and underscores.
USERNAME_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")
REQUEST_TIMEOUT = 5  # seconds, for the optional IP-geolocation lookup


def detect_profile(request):
    if request.method != "POST":
        return render(request, "instagram/home.html")

    username = request.POST.get("username", "").strip().lstrip("@")
    if not USERNAME_RE.match(username):
        return render(request, "instagram/detect.html", {
            "error": "Please enter a valid Instagram username "
                     "(letters, numbers, dots and underscores only)."
        })

    L = instaloader.Instaloader()
    try:
        profile = instaloader.Profile.from_username(L.context, username)
    except ProfileNotExistsException:
        error = f"The profile @{username} does not exist."
    except (TooManyRequestsException, ConnectionException, LoginRequiredException) as e:
        error = ("Instagram refused the request (it often rate-limits or blocks "
                 f"anonymous lookups). Please try again later. Details: {e}")
    except Exception as e:  # any other unexpected failure
        error = f"Could not retrieve profile data for @{username}: {e}"
    else:
        error = None

    if error:
        return render(request, "instagram/detect.html", {"error": error})

    # ---- Extract profile data -------------------------------------------
    full_name = profile.full_name or ""
    bio = profile.biography or ""
    followers = profile.followers
    following = profile.followees
    posts = profile.mediacount
    profile_pic = bool(profile.profile_pic_url)
    ip_address = (request.POST.get("ip_address") or "").strip()  # optional

    # ---- Detection logic (5 checks, 1 point each) ----------------------
    reasons_fake = []
    reasons_real = []
    score = 0

    if posts == 0:
        reasons_fake.append("No posts at all — suspicious inactivity.")
    elif posts < 5:
        reasons_fake.append("Very few posts — could be inactive or fake.")
    else:
        reasons_real.append("Active posting — feels real.")
        score += 1

    if followers == 0 or following / (followers + 1) > 2:
        reasons_fake.append("Unusual follower-following ratio.")
    else:
        reasons_real.append("Decent follower count — feels organic.")
        score += 1

    if profile_pic:
        reasons_real.append("Profile picture present — looks personal.")
        score += 1
    else:
        reasons_fake.append("Missing profile picture.")

    if len(bio.strip()) < 10:
        reasons_fake.append("Very short or empty bio.")
    else:
        reasons_real.append("Bio looks real — effort put into the profile.")
        score += 1

    if full_name.strip():
        reasons_real.append("Full name provided — not hiding identity.")
        score += 1
    else:
        reasons_fake.append("No full name — could be suspicious.")

    # ---- Final verdict ---------------------------------------------------
    profile_type = "Fake"
    if score == 5:
        profile_type = "Genuine"
    elif score >= 3:
        profile_type = "Suspicious but Chill"

    # ---- Optional IP-based location data --------------------------------
    geo_data = None
    if ip_address:
        try:
            ipaddress.ip_address(ip_address)  # reject anything that is not a real IP
            response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                data = response.json()
                geo_data = {
                    "ip": ip_address,
                    "location": f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country', '')}",
                }
        except (ValueError, requests.RequestException):
            geo_data = None

    profile_info = {
        "username": username,
        "full_name": full_name,
        "bio": bio,
        "followers": followers,
        "following": following,
        "posts": posts,
    }
    vibe_score = {
        "score": score * 20,  # 0-5 points -> percentage for the visual bar
        "reasons": reasons_real if score >= 3 else reasons_fake,
    }

    return render(request, "instagram/detect.html", {
        "profile": profile_info,
        "vibe_score": vibe_score,
        "profile_type": profile_type,
        "geo": geo_data,
    })

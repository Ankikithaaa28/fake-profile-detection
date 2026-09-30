

import tweepy
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Loading from .env
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

# Tweepy Client
client = tweepy.Client(bearer_token=BEARER_TOKEN)

def get_user_details(username):
    try:
        user = client.get_user(
            username=username,
            user_fields=["profile_image_url", "description", "created_at", "public_metrics"]
        )
        if user.data:
            return user.data
        else:
            return None
    except tweepy.TooManyRequests:
        return "RATE_LIMIT"
    except Exception as e:
        print(f"Error fetching user details: {e}")  # Debug log
        return None

def calculate_fakeness(user):
    score = 0

    # Profile picture check
    if not user.profile_image_url or "default_profile" in user.profile_image_url:
        score += 20

    # Bio check
    if not user.description or len(user.description.strip()) < 5:
        score += 20

    # Followers / Following check
    followers = user.public_metrics.get('followers_count', 0)
    following = user.public_metrics.get('following_count', 0)
    if followers < 10 and following > 500:
        score += 20

    # Tweet count check
    tweets = user.public_metrics.get('tweet_count', 0)
    if tweets < 10:
        score += 20

    # Account age check (timezone-aware fix)
    created_at = user.created_at
    if created_at.tzinfo is None:
        # If somehow tzinfo is missing (unlikely, but safe to check)
        created_at = created_at.replace(tzinfo=timezone.utc)

    account_age_days = (datetime.now(timezone.utc) - created_at).days
    if account_age_days < 90:
        score += 20

    return score

def analyze_user(username):
    user = get_user_details(username)
    
    if user == "RATE_LIMIT":
        return {"error": "Rate Limit Hit. Try after some time."}
    if not user:
        return {"error": "User not found or incomplete data."}

    fakeness = calculate_fakeness(user)
    status = "Fake" if fakeness > 50 else "Real"

    return {
        "username": username,
        "fakeness_percentage": fakeness,
        "status": status,
        "profile_image": user.profile_image_url,
        "bio": user.description or "No Bio Provided",
        "followers": user.public_metrics.get('followers_count', 0),
        "following": user.public_metrics.get('following_count', 0),
        "tweets": user.public_metrics.get('tweet_count', 0),
        "created_at": user.created_at.strftime('%Y-%m-%d')
    }

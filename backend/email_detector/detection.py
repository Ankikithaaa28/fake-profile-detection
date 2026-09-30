
import requests
import re
import dns.resolver # type: ignore

# 
# ---------- Configuration Constants ----------

# Keywords often found in suspicious or temporary usernames
SUSPICIOUS_KEYWORDS = { 
    "fake", "temp", "spam", "test", "bot", "demo", "null", "trash", "asdf", "qwerty", "abc123", "admin123", "noreply",
    "junk", "trial", "invalid", "throwaway", "zzz", "testing", "reset", "signup", "guest", "unknown", "emailtest",
    "delete", "xxx", "abcabc", "tryagain", "temporary", "verify", "noemail", "sample", "sampleuser", "anonym",
    "invaliduser", "example", "deadmail", "ghost", "bypass", "nocontact", "useonce", "blackhole", "singleuse",
    "openmailbox", "instant", "botmail", "robot", "burner", "nologin", "alias", "clickbait", "spamtrap", "throw",
    "disposable", "nospam", "tempmail", "trashmail", "123456", "freeuser", "nobody", "fakename",
    "unverified", "unreal", "notreal", "noname", "nomail", "bogus", "scam", "identity",
    "anonymous", "faker", "user123", "emailme", "hack", "crack", "autobot", "automail",
    "false", "dummy", "preview", "testingonly", "onetime", "deleteafter", "junkmail",
    "tempid", "mailuser", "reject", "remail", "nowhere", "botuser", "nospam4me",
    "tempaccount", "backupmail", "signupnow", "nocare", "freeaccount", "mailfail"
}

# Patterns often found in suspicious usernames (e.g., repetitions, long number sequences)
BLACKLISTED_PATTERNS = [
    r"(.)\1{2,}",          # e.g., aaa, 111
    r"(..)\1{2,}",         # e.g., ababab, 121212
    r"[a-z]{6,}[0-9]{3,}", # e.g., longstring123
    r"^[0-9]{6,}$",        # e.g., 123456 (as full username)
    r"(?:asdf|qwerty|abc123)" # Common keyboard patterns
]

# Domains from major, well-established email providers
TRUSTED_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "live.com",
    "aol.com", "icloud.com", "protonmail.com", "zoho.com"
}

# Common domains that are generally legitimate but might not be "premium" or business-oriented
COMMON_DOMAINS = TRUSTED_DOMAINS.union({
    "gmx.com", "yandex.com", "mail.com", "inbox.com", "rediffmail.com",
    "seznam.cz", "wp.pl", "onet.pl", # Examples of popular regional providers
    "mail.ru", "list.ru", "bk.ru", "internet.ru" # More Russian providers
})

# Domains from known disposable email address providers
DISPOSABLE_DOMAINS = {
    "mailinator.com", "tempmail.com", "10minutemail.com", "guerrillamail.com", "trashmail.com",
    "getnada.com", "moakt.com", "throwawaymail.com", "maildrop.cc", "mintemail.com",
    "fakemail.net", "dispostable.com", "temp-mail.org", "yopmail.com", "burnermail.io",
    "sharklasers.com", "grr.la", "spamgourmet.com", "mailsac.com", "tempmail.net",
    "tmail.ws", "emeil.ir", "fmail.nu", "anonmail.net", "temporarymail.com"
    # Add more known disposable domains
}

# Mapping of TLDs to countries or general types
TLD_COUNTRY_MAPPING = {
    'com': 'US (Global)', 'org': 'Non-Profit (Global)', 'net': 'Network (Global)',
    'edu': 'Educational (US)', 'gov': 'Government (US)', 'mil': 'Military (US)',
    'co.uk': 'UK', 'uk': 'UK', 'de': 'Germany', 'fr': 'France', 'in': 'India',
    'ca': 'Canada', 'jp': 'Japan', 'au': 'Australia', 'cn': 'China', 'ru': 'Russia',
    'br': 'Brazil', 'nl': 'Netherlands', 'it': 'Italy', 'es': 'Spain', 'ch': 'Switzerland',
    'se': 'Sweden', 'no': 'Norway', 'fi': 'Finland', 'dk': 'Denmark', 'pl': 'Poland',
    'za': 'South Africa', 'nz': 'New Zealand', 'kr': 'South Korea', 'sg': 'Singapore',
    'my': 'Malaysia', 'th': 'Thailand', 'vn': 'Vietnam', 'id': 'Indonesia',
    'ph': 'Philippines', 'hk': 'Hong Kong', 'tw': 'Taiwan', 'ie': 'Ireland',
    'at': 'Austria', 'be': 'Belgium', 'pt': 'Portugal', 'gr': 'Greece',
    'cz': 'Czech Republic', 'hu': 'Hungary', 'ro': 'Romania', 'ua': 'Ukraine',
    'tr': 'Turkey', 'il': 'Israel', 'ae': 'United Arab Emirates', 'sa': 'Saudi Arabia',
    'eg': 'Egypt', 'ng': 'Nigeria', 'mx': 'Mexico', 'ar': 'Argentina', 'cl': 'Chile',
    'co': 'Colombia', 'pe': 'Peru',
    'io': 'British Indian Ocean Territory (Tech)', 'ai': 'Anguilla (AI/Tech)',
    'ly': 'Libya (URL Shorteners)', 'is': 'Iceland', 'info': 'Informational (Global)',
    'biz': 'Business (Global)', 'tv': 'Tuvalu (Media/Streaming)', 'me': 'Montenegro (Personal/Tech)',
    'xyz': 'General Purpose (Often Low-Cost/Spam)', 'online': 'General Purpose (Often Low-Cost/Spam)',
    'site': 'General Purpose (Often Low-Cost/Spam)', 'club': 'General Purpose',
    'top': 'General Purpose (Often Low-Cost/Spam)', 'bid': 'General Purpose (Often Spam)',
    'loan': 'Financial (Often Spam/Scam)', 'date': 'Dating (Often Spam)', 'review': 'Review (Often Spam)',
    'party': 'Entertainment (Often Spam)', 'science': 'Science (Less common)', 'work': 'Work (Less common)'
    # Add more as needed
}

# Penalty scores for specific TLDs known for higher risk or spam association
SUSPICIOUS_TLD_PENALTIES = {
    'xyz': 3, 'top': 3, 'online': 2, 'site': 2, 'club': 2, 'live': 1, # .live can be legit but also abused
    'stream': 3, 'loan': 4, 'date': 3, 'review': 3, 'party': 3, 'bid': 3,
    # Add more TLDs and their associated penalty scores
}

# Common prefixes for role-based email accounts
ROLE_BASED_PREFIXES = {
    "info", "admin", "administrator", "support", "contact", "sales", "hr", "jobs", "careers",
    "webmaster", "postmaster", "noreply", "no-reply", "help", "service", "billing",
    "abuse", "security", "marketing", "press", "media", "feedback", "test", "demo",
    "office", "manager", "director", "president", "ceo", "editor", "subscribe", "unsubscribe"
}


# ---------- Utility Functions ----------
REQUEST_TIMEOUT = 5 # seconds for HTTP requests

def check_domain_web_presence(domain: str) -> bool:
    """
    Checks if a domain has an active website by trying HTTP/HTTPS GET requests.
    Returns True if a 2xx or 3xx response (after redirects) is received, False otherwise.
    """
    protocols = [f"https://{domain}", f"http://{domain}"]
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 FakeProfileDetectorBot/1.0'
    }
    for url in protocols:
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT, headers=headers, allow_redirects=True)
            # Consider 2xx (success) and 3xx (redirects resolved to success) as signs of an active web presence.
            if 200 <= response.status_code < 400:
                return True
        except requests.exceptions.RequestException:
            # Covers ConnectionError, Timeout, TooManyRedirects, SSL errors etc.
            continue # Try next protocol or fail if all attempts fail
    return False

def get_country_from_domain(domain: str) -> str:
    """Guesses the country or type based on the domain's TLD."""
    parts = domain.split('.')
    if len(parts) > 1:
        # Check for two-part TLDs first (e.g., co.uk)
        if len(parts) > 2 and f"{parts[-2]}.{parts[-1]}" in TLD_COUNTRY_MAPPING:
            tld = f"{parts[-2]}.{parts[-1]}"
            return TLD_COUNTRY_MAPPING[tld]
        # Check for single-part TLD
        tld = parts[-1]
        return TLD_COUNTRY_MAPPING.get(tld, f"Unknown TLD ({tld})")
    return "Unknown (Malformed Domain)"

def has_mx_record(domain: str) -> bool:
    """Checks if a domain has MX (Mail Exchange) records."""
    try:
        # Use the DNS resolver to check for MX records
        dns.resolver.resolve(domain, 'MX') # type: ignore
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.LifetimeTimeout, dns.resolver.YXDOMAIN): # type: ignore
        return False
    except Exception: # Catch any other unexpected DNS errors
        # Log this exception in a real application
        return False

def is_gibberish_username(username: str, threshold_consonant_ratio: float = 0.7, min_len_for_check: int = 6) -> bool:
    """Simple check for gibberish based on consonant ratio or consecutive consonants/vowels."""
    if len(username) < min_len_for_check:
        return False

    vowels = "aeiou"
    consonants = "bcdfghjklmnpqrstvwxyz"
    num_vowels = sum(1 for char in username if char in vowels)
    num_consonants = sum(1 for char in username if char in consonants)

    total_letters = num_vowels + num_consonants
    if total_letters == 0:
        return True # Username has no letters, could be random symbols/numbers

    # Check consonant ratio
    if num_consonants / total_letters > threshold_consonant_ratio:
        return True

    # Check for excessive consecutive consonants or vowels
    if re.search(r'[bcdfghjklmnpqrstvwxyz]{4,}', username): return True # 4+ consecutive consonants
    if re.search(r'[aeiou]{4,}', username): return True # 4+ consecutive vowels (less common for gibberish but unusual)

    # Check for unusual character sequences (e.g., zxcvbn) - basic
    if re.search(r'(?:zxcv|qwer|poiu|lkjh|mnbv)', username): return True

    return False


def analyze_username(username: str) -> tuple[int, list[str]]:
    """Analyzes the username part of an email for suspicious characteristics."""
    penalty_score = 0
    reasons = []

    # Length check
    if len(username) < 4 or len(username) > 30: # Adjusted length constraints
        penalty_score += 2
        reasons.append(f"Unusual username length ({len(username)} characters).")

    # Numeric username
    if username.isdigit():
        penalty_score += 3 # Increased penalty for all-numeric usernames
        reasons.append("Username consists only of numbers.")

    # Blacklisted patterns
    if any(re.search(pat, username) for pat in BLACKLISTED_PATTERNS):
        penalty_score += 3 # Increased penalty for blacklisted patterns
        reasons.append("Suspicious pattern detected in username.")

    # Suspicious keywords
    # username is already lowercased when passed to this function
    if any(keyword in username for keyword in SUSPICIOUS_KEYWORDS):
        penalty_score += 6 # High penalty for suspicious keywords
        reasons.append("Suspicious keyword found in username.")

    # Unusual characters (allow alphanumeric, dot, underscore, hyphen)
    if re.search(r'[^a-zA-Z0-9._-]', username):
        penalty_score += 2
        reasons.append("Username contains unusual characters (other than letters, numbers, '.', '_', '-').")

    # Excessive special characters
    if username.count('.') > 3 or username.count('_') > 3 or username.count('-') > 3:
        penalty_score += 2
        reasons.append("Username contains an excessive number of special characters ('.', '_', '-').")

    # Role-based username check
    # Check the part before the first dot or underscore as well
    username_part_for_role_check = username.split('.')[0].split('_')[0]
    if username_part_for_role_check in ROLE_BASED_PREFIXES:
        reasons.append(f"ℹ️ Username '{username_part_for_role_check}' appears to be a role-based account.")
        # Optional: Add penalty if role-based on non-corporate/trusted domain
        # if not is_trusted_provider and not is_common_provider: # Requires passing domain info
        #     penalty_score += 1

    # Gibberish check
    if is_gibberish_username(username):
        penalty_score += 4 # Increased penalty for gibberish
        reasons.append("Username appears to be gibberish or random characters.")

    # Max score for username analysis is roughly 2+3+3+6+2+2+4 = 22

    return penalty_score, reasons

# ---------- Core Detection Logic ----------

def detect_email_profile(email: str) -> dict:
    """
    Analyzes an email address to determine its likelihood of being fake.
    Returns a dictionary with analysis details.
    """
    result = {
        "email": email,
        "is_valid_format": False,
        "is_fake": False,
        "final_score": 0, # This will be the total penalty score
        "reasons": [],
        "verdict": "Analysis pending...",
        "emoji": "🤔",
        "fake_percentage": "0%",
        "domain": "N/A",
        "country_tld_info": "N/A",
        "is_trusted_provider": False, # Initialize for the result
        "score_percent_numeric": 0.0  # Initialize for the result
    }
    total_penalty_score = 0

    # --- Input Validation and Normalization ---
    if not email or not isinstance(email, str):
        result.update({
            "is_fake": True,
            "reasons": ["❌ Invalid input: Email is missing or not a string."],
            "verdict": "Invalid input.", "emoji": "🚫",
            "final_score": 100, "score_percent_numeric": 100.0,
            "fake_percentage": "100%"
        })
        return result

    email_lower = email.lower().strip() # Normalize email
    result["email"] = email # Store original for display

    # More robust regex for email format validation
    # Allows for internationalized domain names (IDNs) in a basic way by not restricting TLD too much
    # Also allows '+' in username for aliases
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(email_regex, email_lower):
        result.update({
            "is_fake": True,
            "reasons": ["❌ Invalid email format (e.g., bad characters, missing '@' or domain, invalid TLD structure)."],
            "verdict": "Totally fake. Invalid format.",
            "emoji": "❌", "score_percent_numeric": 100.0,
            "final_score": 100, # Max penalty for invalid format
            "fake_percentage": "100%"
        })
        return result

    result["is_valid_format"] = True
    result["reasons"].append("✅ Email format appears valid.")

    try:
        username, domain = email_lower.split('@', 1)
        result["domain"] = domain
    except ValueError:
        # This case should ideally be caught by the regex, but as a fallback:
        result.update({
            "is_fake": True,
            "reasons": ["❌ Critical error: Could not extract username and domain despite passing regex. Please check email structure."],
            "verdict": "Format error.",
            "emoji": "❌", "score_percent_numeric": 100.0,
            "final_score": 100,
            "fake_percentage": "100%"
        })
        return result

    # --- Domain Classification ---
    is_trusted_provider = False # Local variable for logic within this function
    is_common_provider = False

    if domain in DISPOSABLE_DOMAINS:
        total_penalty_score += 10
        result["reasons"].append(f"🚫 High risk: Domain '{domain}' is a known disposable email provider.")
    elif domain in TRUSTED_DOMAINS:
        # No penalty for trusted domains
        result["reasons"].append(f"✅ Low risk: Domain '{domain}' is a trusted provider.")
        is_trusted_provider = True
        result["is_trusted_provider"] = True # Set the flag in the result dictionary
    elif domain in COMMON_DOMAINS:
        total_penalty_score += 2 # Slight penalty for common but not top-tier/business
        result["reasons"].append(f"⚠️ Medium risk: Domain '{domain}' is common but not a top-tier provider.")
        is_common_provider = True
    else: # Unknown or uncommon domain - check for web presence
        # For unknown domains, check web presence. MX check is handled separately and more definitively.
        # This helps differentiate between completely obscure domains and those with some web footprint
        # (like many legitimate organizational domains, e.g., oracle.com).
        if check_domain_web_presence(domain):
            total_penalty_score += 2 # Reduced penalty if it has a website, even if unknown.
            result["reasons"].append(f"ℹ️ Domain '{domain}' is not in predefined lists but appears to have an active website. MX records will be checked separately.")
        else:
            total_penalty_score += 4 # Higher penalty if unknown AND no clear web presence.
            result["reasons"].append(f"⚠️ Medium-High risk: Domain '{domain}' is uncommon and no active website was readily found. MX records will be checked separately.")
    # --- TLD/Country Info ---
    country_tld_info = get_country_from_domain(domain)
    result["country_tld_info"] = country_tld_info
    result["reasons"].append(f"ℹ️ Domain TLD/Country Info: {country_tld_info}.")

    # --- Suspicious TLD Penalty ---
    domain_parts = domain.split('.')
    tld_for_penalty_check = domain_parts[-1] if len(domain_parts) > 1 else ""
    if tld_for_penalty_check in SUSPICIOUS_TLD_PENALTIES:
        penalty = SUSPICIOUS_TLD_PENALTIES[tld_for_penalty_check]
        total_penalty_score += penalty
        result["reasons"].append(f"⚠️ Medium risk: TLD '.{tld_for_penalty_check}' often associated with spam/low-trust (Penalty: +{penalty}).")

    # --- MX Record Check ---
    if has_mx_record(domain):
        result["reasons"].append(f"✅ MX records found for domain '{domain}'.")
    else:
        # Don't penalize too harshly if it's a trusted domain that might have other verification (though rare for MX)
        # But for others, it's a strong indicator.
        if not is_trusted_provider: # Apply higher penalty if not a known trusted provider
            total_penalty_score += 5
            result["reasons"].append(f"⚠️ High risk: No MX records found for domain '{domain}'. Email delivery likely to fail.")
        else:
            total_penalty_score += 2 # Lower penalty for trusted providers, but still note it
            result["reasons"].append(f"🤔 Medium risk: No MX records found for trusted domain '{domain}'. This is unusual.")

    # --- Username Analysis ---
    # Pass the original case username if desired for specific checks, or lowercased
    uname_score, uname_reasons = analyze_username(username) # username is already lowercased
    total_penalty_score += uname_score
    result["reasons"].extend(uname_reasons)

    # --- Fake-o-Meter Calculation ---
    # Estimate Max possible penalty:
    # Disposable (10) + No MX (5) + Suspicious TLD (max 4) + Username (approx 22) = ~41
    # Using a divisor that reflects this potential max penalty to normalize the percentage.
    MAX_EXPECTED_PENALTY_SCORE = 45 # Adjusted divisor based on potential max score

    fake_percent = 0.0 # Use float for precision
    if MAX_EXPECTED_PENALTY_SCORE > 0:
        # Ensure total_penalty_score doesn't exceed MAX_EXPECTED_PENALTY_SCORE for percentage calculation
        clamped_score = min(total_penalty_score, MAX_EXPECTED_PENALTY_SCORE)
        fake_percent = min(100.0, (clamped_score / MAX_EXPECTED_PENALTY_SCORE) * 100.0)

    result["fake_percentage"] = f"{int(round(fake_percent))}%" # Display as rounded int string
    result["score_percent_numeric"] = fake_percent # Store the float numeric percentage
    result["final_score"] = total_penalty_score # This is the raw penalty score

    # --- Verdict ---
    if fake_percent >= 75: # Adjusted threshold for "very likely fake"
        result.update({
            "is_fake": True,
            "verdict": "🚩 Very likely fake or high-risk.",
            "emoji": "🚩"
        })
    elif fake_percent >= 10: # Lowered threshold for "possibly suspicious"
        result.update({
            "is_fake": True, # Mark as fake to reflect suspicion in status
            "verdict": "🧐 Possibly suspicious. Exercise caution.",
            "emoji": "🧐"
        })
    else: # < 10%
        result.update({
            "is_fake": False,
            "verdict": "✅ Appears to be a legitimate email.",
            "emoji": "✅"
        })
        # Add a special verdict for emails with zero penalty from trusted providers
        if total_penalty_score == 0 and is_trusted_provider:
             result["verdict"] = "✅ Looks highly legitimate." # This will override the above verdict
             result["emoji"] = "✅" # Ensure emoji is consistent for this case


    return result

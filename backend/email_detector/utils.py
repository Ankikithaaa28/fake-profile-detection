

# email_detector/utils.py

import dns.resolver
TRUSTED_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com", "rediffmail.com"]
DISPOSABLE_DOMAINS = ["mailinator.com", "10minutemail.com", "temp-mail.org", "guerrillamail.com"]


def guess_country(domain: str) -> str:
    tld_country_mapping = {
        'com': 'US',
        'co.uk': 'UK',
        'de': 'Germany',
        'fr': 'France',
        'in': 'India',
        'ca': 'Canada',
        'jp': 'Japan',
        'au': 'Australia',
    }
    tld = domain.split('.')[-1]
    return tld_country_mapping.get(tld, 'Unknown')

def has_mx_record(domain: str) -> bool:
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.LifetimeTimeout):
        return False

def is_suspicious_domain(domain: str) -> bool:
    return any(disposable_domain in domain for disposable_domain in DISPOSABLE_DOMAINS)

def get_domain_from_email(email: str) -> str:
    return email.split('@')[-1].lower().strip()
    
COMMON_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "icloud.com", "aol.com",
    "rediffmail.com", "hotmail.com", "live.com", "msn.com"
]
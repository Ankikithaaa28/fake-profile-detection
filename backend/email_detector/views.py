

from django.shortcuts import render

# Create your views here.
from django.shortcuts import render
from .detection import detect_email_profile, get_country_from_domain # Assuming get_country_from_domain is in detection.py

def email_landing_page(request):
    """
    Serves the initial page with the email input form.
    The detect.html template should contain the form.
    """
    return render(request, 'email_page.html')  # Your intro page

def detect_email(request):
    """
    Handles the email detection request from the form submission
    and displays the analysis results.
    """
    context = {"result": None}

    if request.method == "POST":
        email_username = request.POST.get("email_username", "").strip().lower()
        selected_domain_option = request.POST.get("email_domain", "").lower() # e.g., "@gmail.com" or "other"
        
        domain_part = "" # This will be the domain without '@'

        if selected_domain_option == "other":
            custom_domain_input = request.POST.get("custom_email_domain", "").strip().lower()
            if custom_domain_input:
                # Remove '@' if user typed it, as we'll add it consistently later
                domain_part = custom_domain_input.lstrip('@') 
        elif selected_domain_option.startswith('@'):
            domain_part = selected_domain_option[1:] # Remove the leading '@'
        elif selected_domain_option: # Should not happen if HTML select is correct, but as a fallback
            domain_part = selected_domain_option 

        # Proceed if we have both a username and a valid domain part
        if email_username and domain_part:
            full_email = f"{email_username}@{domain_part}"
            raw_result = detect_email_profile(full_email)
            
            # Ensure 'score_percent_numeric' and 'is_trusted_provider' are in raw_result.
            # Ideally, detect_email_profile should always provide these.
            # Adding fallbacks here just in case, but it's better to fix in detection.py.
            if 'score_percent_numeric' not in raw_result and 'fake_percentage' in raw_result:
                try:
                    numeric_part = raw_result['fake_percentage'].replace('%', '')
                    raw_result['score_percent_numeric'] = float(numeric_part)
                except ValueError:
                    raw_result['score_percent_numeric'] = 0 
            elif 'score_percent_numeric' not in raw_result:
                 raw_result['score_percent_numeric'] = 0

            if 'is_trusted_provider' not in raw_result:
                raw_result['is_trusted_provider'] = False # Default if missing

            context["result"] = raw_result
        
        # Handle cases with missing input
        elif email_username and not domain_part:
            context["result"] = {
                "email": email_username, "is_valid_format": False, "is_fake": True, 
                "final_score": 100, "score_percent_numeric": 100,
                "reasons": ["❌ Invalid input: Domain part is missing or invalid."],
                "verdict": "Invalid input. Domain missing.", "emoji": "🚫", 
                "fake_percentage": "100%", "domain": "N/A", "country_tld_info": "N/A",
                "is_trusted_provider": False
            }
        elif not email_username and domain_part:
            context["result"] = {
                "email": f"@{domain_part}", "is_valid_format": False, "is_fake": True,
                "final_score": 100, "score_percent_numeric": 100,
                "reasons": ["❌ Invalid input: Username part is missing."],
                "verdict": "Invalid input. Username missing.", "emoji": "🚫",
                "fake_percentage": "100%", "domain": domain_part,
                "country_tld_info": get_country_from_domain(domain_part), # Try to get country for domain
                "is_trusted_provider": False
            }
        else: # Both are empty or invalid combination
            context["result"] = {
                "email": "", "is_valid_format": False, "is_fake": True,
                "final_score": 100, "score_percent_numeric": 100,
                "reasons": ["❌ Invalid input: Email username and/or domain are missing."],
                "verdict": "Invalid input. Email empty.", "emoji": "🚫",
                "fake_percentage": "100%", "domain": "N/A", "country_tld_info": "N/A",
                "is_trusted_provider": False
            }
            
    return render(request, "email_detector/detect.html", context)

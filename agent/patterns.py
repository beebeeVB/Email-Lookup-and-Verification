"""
Scrapes email-format.com to get the verified email pattern for a domain.
Falls back to a ranked list of common patterns if the domain isn't indexed.
"""

import re
import time
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}

# Ordered by global prevalence — used as fallback candidates
FALLBACK_PATTERNS = [
    "{first}.{last}",
    "{f}{last}",
    "{first}{last}",
    "{first}_{last}",
    "{first}",
    "{f}.{last}",
]


def get_pattern(domain: str) -> list[str]:
    """
    Returns a list of email format strings for the domain, most likely first.
    Each string uses {first}, {last}, {f} placeholders.
    If email-format.com has it, returns that. Otherwise returns ranked fallbacks.
    """
    time.sleep(1.5)
    url = f"https://www.email-format.com/d/{domain}/"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return FALLBACK_PATTERNS

        soup = BeautifulSoup(r.text, "html.parser")

        # email-format.com lists patterns with percentage usage
        # they appear in <td> cells with format strings like {first}.{last}
        patterns_found = []
        for td in soup.find_all("td"):
            text = td.get_text(strip=True)
            if "{" in text and "}" in text:
                # normalize their notation to ours
                normalized = (
                    text
                    .replace("%first%", "{first}")
                    .replace("%last%", "{last}")
                    .replace("%f%", "{f}")
                    .replace("%l%", "{l}")
                )
                if "{first}" in normalized or "{f}" in normalized:
                    patterns_found.append(normalized)

        if patterns_found:
            print(f"  [pattern] {domain} → {patterns_found[0]} (from email-format.com)")
            return patterns_found

        print(f"  [pattern] {domain} → not indexed, using fallbacks")
        return FALLBACK_PATTERNS

    except Exception as e:
        print(f"  [pattern] error for {domain}: {e}")
        return FALLBACK_PATTERNS


def build_email(first: str, last: str, domain: str, pattern: str) -> str:
    """
    Constructs a candidate email from a pattern string.
    e.g. pattern="{first}.{last}", domain="example.com" → "john.smith@example.com"
    """
    first = first.lower().strip()
    last = last.lower().strip()

    local = (
        pattern
        .replace("{first}", first)
        .replace("{last}", last)
        .replace("{f}", first[0])
        .replace("{l}", last[0])
    )
    return f"{local}@{domain}"

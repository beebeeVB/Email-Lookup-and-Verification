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

# Standard permutations ranked by global corporate prevalence
STANDARD_PATTERNS = [
    "{f}.{l}",
    "{fi}{l}",
    "{f}_{l}",
    "{f}{l}",
    "{fi}.{l}",
    "{f}",
]


def _scrape_domain_pattern(domain: str) -> str | None:
    """
    Hits email-format.com to get the verified pattern for this specific domain.
    Returns the top pattern string or None if not indexed.
    """
    try:
        time.sleep(1.2)
        r = requests.get(
            f"https://www.email-format.com/d/{domain}/",
            headers=HEADERS,
            timeout=10
        )
        if r.status_code != 200:
            return None
        soup = BeautifulSoup(r.text, "html.parser")
        for td in soup.find_all("td"):
            text = td.get_text(strip=True)
            if "%" in text and ("first" in text or "last" in text):
                return text  # raw pattern from site e.g. %first%.%last%
        return None
    except Exception:
        return None


def _pattern_to_email(pattern: str, first: str, last: str, domain: str) -> str:
    """Converts any pattern notation to a real email address."""
    # our internal notation
    local = (
        pattern
        .replace("{f}", first)
        .replace("{l}", last)
        .replace("{fi}", first[0])
        .replace("{li}", last[0])
    )
    # email-format.com notation
    local = (
        local
        .replace("%first%", first)
        .replace("%last%", last)
        .replace("%f%", first[0])
        .replace("%l%", last[0])
    )
    return f"{local}@{domain}"


def generate_candidates(first: str, last: str, domain: str) -> list[str]:
    """
    Returns an ordered list of candidate email addresses.
    If email-format.com has the domain indexed, that pattern goes first.
    Otherwise falls back to standard permutations.
    """
    f = first.lower().strip()
    l = last.lower().strip()
    d = domain.lower().strip()

    candidates = []

    # try to get verified pattern for this domain
    scraped = _scrape_domain_pattern(d)
    if scraped:
        top = _pattern_to_email(scraped, f, l, d)
        candidates.append(top)
        print(f"  [pattern] {d} → {scraped} (from email-format.com)")
    else:
        print(f"  [pattern] {d} → not indexed, using standard permutations")

    # append all standard permutations as fallback candidates
    for p in STANDARD_PATTERNS:
        email = _pattern_to_email(p, f, l, d)
        if email not in candidates:
            candidates.append(email)

    return candidates

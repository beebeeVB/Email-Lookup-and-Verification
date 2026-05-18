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

# 100 patterns ranked by global corporate prevalence
# Tokens: {f}=first, {l}=last, {fi}=first initial, {li}=last initial
# {f3}/{f4} = first 3/4 chars of first name, {l3}/{l4} = first 3/4 of last
STANDARD_PATTERNS = [
    # Tier 1: covers ~85% of corporate domains
    "{f}.{l}",
    "{fi}{l}",
    "{f}_{l}",
    "{f}{l}",
    "{fi}.{l}",
    "{f}",
    "{l}",
    "{f}.{li}",
    "{fi}{li}",
    "{fi}.{li}",

    # Tier 2: less common but widely used
    "{l}.{f}",
    "{l}_{f}",
    "{l}{f}",
    "{l}{fi}",
    "{l}.{fi}",
    "{l}_{fi}",
    "{f}-{l}",
    "{l}-{f}",
    "{fi}-{l}",
    "{f}.{l}1",

    # Tier 3: initial combos
    "{fi}{l}1",
    "{f}1",
    "{f}_{li}",
    "{fi}_{l}",
    "{fi}_{li}",
    "{f}{li}",
    "{li}{f}",
    "{li}.{f}",
    "{li}_{f}",
    "{li}{fi}",

    # Tier 4: positional variants
    "{f}.{l}01",
    "{fi}{l}01",
    "{f}{l}1",
    "{f}_{l}1",
    "{f}-{l}1",
    "{l}{f}1",
    "{f}.{l}2",
    "{fi}{l}2",
    "{f}2",
    "{l}1",

    # Tier 5: dot and dash combos
    "{fi}_{f}_{l}",
    "{f}_{l}_{fi}",
    "{l}_{f}_{fi}",
    "{fi}_{li}_{f}",
    "{f}_{li}_{l}",
    "{li}_{fi}_{f}",
    "{f}_{l}_01",
    "{fi}_{l}_01",
    "{f}_{l}_1",
    "{fi}_{l}_1",

    # Tier 6: underscore heavy
    "{f}--{l}",
    "{l}--{f}",
    "{f}.{l}-{fi}",
    "{fi}-{l}-{f}",
    "{l}--{fi}",
    "{fi}--{l}",
    "{f}-{li}",
    "{l}-{fi}",
    "{fi}-{li}",
    "{l}-{f}-{fi}",

    # Tier 7: truncated first name variants
    "{f3}{l}",
    "{f3}.{l}",
    "{f3}_{l}",
    "{f3}-{l}",
    "{f4}{l}",
    "{f4}.{l}",
    "{f4}_{l}",
    "{l}{f3}",
    "{l}.{f3}",
    "{l}_{f3}",

    # Tier 8: truncated last name variants
    "{f}{l3}",
    "{f}.{l3}",
    "{f}_{l3}",
    "{fi}{l3}",
    "{fi}.{l3}",
    "{l3}{f}",
    "{l3}.{f}",
    "{l3}_{f}",
    "{l4}{f}",
    "{l4}.{f}",

    # Tier 9: numeric suffixes for orgs with name collisions
    "{f}.{l}001",
    "{fi}{l}001",
    "{f}{l}001",
    "{f}.{l}100",
    "{fi}{l}100",
    "{f}.{l}99",
    "{fi}{l}99",
    "{f}.{l}123",
    "{fi}{l}123",
    "{f}{l}123",

    # Tier 10: regional and edge patterns
    "{l}{fi}1",
    "{l}.{fi}1",
    "{f}.{l}{li}",
    "{fi}{l}{li}",
    "{f}{fi}{l}",
    "{l}{f}{fi}",
    "{fi}.{l}.ext",
    "info.{fi}{l}",
    "contact.{fi}{l}",
    "{f}.{l}.{fi}",
]


def _scrape_domain_pattern(domain: str) -> str | None:
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
                return text
        return None
    except Exception:
        return None


def _pattern_to_email(pattern: str, first: str, last: str, domain: str) -> str:
    f3 = first[:3]
    f4 = first[:4]
    l3 = last[:3]
    l4 = last[:4]

    local = (
        pattern
        .replace("{f3}", f3)
        .replace("{f4}", f4)
        .replace("{l3}", l3)
        .replace("{l4}", l4)
        .replace("{f}", first)
        .replace("{l}", last)
        .replace("{fi}", first[0])
        .replace("{li}", last[0])
        # email-format.com notation
        .replace("%first%", first)
        .replace("%last%", last)
        .replace("%f%", first[0])
        .replace("%l%", last[0])
    )
    return f"{local}@{domain}"


def generate_candidates(first: str, last: str, domain: str) -> list[str]:
    f = first.lower().strip()
    l = last.lower().strip()
    d = domain.lower().strip()

    candidates = []

    scraped = _scrape_domain_pattern(d)
    if scraped:
        top = _pattern_to_email(scraped, f, l, d)
        candidates.append(top)
        print(f"  [pattern] {d} -> {scraped} (from email-format.com)")
    else:
        print(f"  [pattern] {d} -> not indexed, trying 100 permutations")

    for p in STANDARD_PATTERNS:
        email = _pattern_to_email(p, f, l, d)
        if email not in candidates:
            candidates.append(email)

    return candidates

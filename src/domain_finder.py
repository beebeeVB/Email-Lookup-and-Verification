"""
Given a company name, finds its primary email domain.
Uses Google search to find the official website, then extracts the domain.
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


def _google_first_url(query: str) -> str | None:
    time.sleep(2.0)
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num=5"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/url?q=" in href:
                clean = href.split("/url?q=")[1].split("&")[0]
                if any(skip in clean for skip in [
                    "google.", "youtube.", "linkedin.", "facebook.",
                    "twitter.", "wikipedia.", "bloomberg.", "crunchbase."
                ]):
                    continue
                if clean.startswith("http"):
                    return clean
        return None
    except Exception:
        return None


def _extract_domain(url: str) -> str | None:
    match = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if match:
        return match.group(1).lower()
    return None


def find_domain(company: str) -> str | None:
    """
    Searches Google for the company's official website and returns its domain.
    e.g. "amfori" -> "amfori.org"
    """
    url = _google_first_url(f"{company} official website")
    if url:
        domain = _extract_domain(url)
        if domain:
            print(f"  [domain] {company} -> {domain}")
            return domain

    # fallback: try without "official website"
    url = _google_first_url(company)
    if url:
        domain = _extract_domain(url)
        if domain:
            print(f"  [domain] {company} -> {domain} (fallback)")
            return domain

    print(f"  [domain] could not find domain for {company}")
    return None


def parse_paste(text: str) -> list[dict]:
    """
    Parses a pasted block of names and companies.
    Accepts formats like:
      Mathias Luyten, amfori
      Jane Smith - Bureau Veritas
      Evan Smith | WRAP
    Returns list of dicts with first_name, last_name, company.
    Domain is looked up separately.
    """
    results = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # split on comma, dash, or pipe
        parts = re.split(r"[,\-\|]", line, maxsplit=1)
        if len(parts) < 2:
            continue

        name_part = parts[0].strip()
        company_part = parts[1].strip()

        name_tokens = name_part.split()
        if len(name_tokens) < 2:
            continue

        first = name_tokens[0]
        last = " ".join(name_tokens[1:])

        results.append({
            "first_name": first,
            "last_name": last,
            "company": company_part,
            "domain": None,
            "role": ""
        })

    return results

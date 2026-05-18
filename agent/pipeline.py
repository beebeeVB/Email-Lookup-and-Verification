"""
Orchestrates the full pipeline for one target:
  1. Get domain email patterns
  2. Construct candidate emails (tries each pattern)
  3. SMTP verify each until one returns 'valid'
  4. Returns the result dict
"""

import time
from agent.patterns import get_pattern, build_email
from agent.smtp import verify


def process(name: str, company: str, domain: str, role: str) -> dict:
    """
    name    — full name e.g. "Sarah Chen"
    company — company name (for logging only)
    domain  — bare domain e.g. "wrap.org"
    role    — job title (for logging only)
    """
    parts = name.strip().split()
    first = parts[0]
    last = parts[-1]

    result = {
        "name": name,
        "company": company,
        "role": role,
        "domain": domain,
        "email": None,
        "status": None,
        "pattern_used": None,
    }

    print(f"\n[→] {name} | {role} @ {company} ({domain})")

    patterns = get_pattern(domain)

    for pattern in patterns:
        candidate = build_email(first, last, domain, pattern)
        print(f"  [try] {candidate}")

        status = verify(candidate)
        print(f"  [smtp] {status}")

        if status == "valid":
            result["email"] = candidate
            result["status"] = "valid"
            result["pattern_used"] = pattern
            print(f"  [✓] confirmed: {candidate}")
            return result

        if status == "catch_all":
            # server accepts everything — record first candidate, flag as catch_all
            result["email"] = candidate
            result["status"] = "catch_all"
            result["pattern_used"] = pattern
            print(f"  [~] catch_all domain — best guess: {candidate}")
            return result

        if status == "unreachable":
            result["status"] = "unreachable"
            print(f"  [✗] mail server unreachable for {domain}")
            return result

        # invalid — try next pattern
        time.sleep(0.8)

    # exhausted all patterns
    result["status"] = "not_found"
    return result

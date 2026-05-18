"""
Verifies whether an email address actually exists by doing a direct
SMTP handshake with the domain's mail server.

No API. No cost. Real result.

Returns one of:
  "valid"       — mailbox confirmed open
  "invalid"     — mailbox rejected (hard bounce)
  "catch_all"   — server accepts everything (can't distinguish real from fake)
  "unreachable" — MX record missing or server timed out
  "error"       — unexpected failure
"""

import smtplib
import socket
import dns.resolver

FROM_ADDRESS = "verify@tamor.ai"  # the address we pretend to send from


def _get_mx(domain: str) -> str | None:
    """Returns the highest-priority MX hostname for the domain."""
    try:
        records = dns.resolver.resolve(domain, "MX")
        records_sorted = sorted(records, key=lambda r: r.preference)
        return str(records_sorted[0].exchange).rstrip(".")
    except Exception:
        return None


def _is_catch_all(domain: str, mx_host: str) -> bool:
    """
    Tests with a provably nonexistent address.
    If the server accepts it, it's a catch-all.
    """
    fake_email = f"zzz_no_such_user_xkq29@{domain}"
    try:
        with smtplib.SMTP(timeout=10) as smtp:
            smtp.connect(mx_host, 25)
            smtp.ehlo_or_helo_if_needed()
            smtp.mail(FROM_ADDRESS)
            code, _ = smtp.rcpt(fake_email)
            return code == 250
    except Exception:
        return False


def verify(email: str) -> str:
    """
    Main verification entry point.
    Returns 'valid', 'invalid', 'catch_all', 'unreachable', or 'error'.
    """
    domain = email.split("@")[1]

    mx_host = _get_mx(domain)
    if not mx_host:
        return "unreachable"

    # catch-all check first — if true, no point checking the real address
    if _is_catch_all(domain, mx_host):
        return "catch_all"

    try:
        with smtplib.SMTP(timeout=10) as smtp:
            smtp.connect(mx_host, 25)
            smtp.ehlo_or_helo_if_needed()
            smtp.mail(FROM_ADDRESS)
            code, message = smtp.rcpt(email)

            if code == 250:
                return "valid"
            elif code in (550, 551, 553):
                return "invalid"
            else:
                return f"unknown_code_{code}"

    except smtplib.SMTPConnectError:
        return "unreachable"
    except smtplib.SMTPServerDisconnected:
        return "unreachable"
    except socket.timeout:
        return "unreachable"
    except Exception as e:
        return f"error: {str(e)[:60]}"

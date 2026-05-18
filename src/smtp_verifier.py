import smtplib
import socket

SENDER = "verify@tamor.ai"


def _check_address(mx_server: str, email: str) -> str:
    """Raw SMTP handshake. Returns VALID, INVALID, or status code string."""
    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_server, 25)
        server.ehlo_or_helo_if_needed()
        server.mail(SENDER)
        code, _ = server.rcpt(email)
        server.quit()

        if code == 250:
            return "VALID"
        elif code in (550, 551, 553):
            return "INVALID"
        else:
            return f"CODE_{code}"
    except smtplib.SMTPConnectError:
        return "UNREACHABLE"
    except socket.timeout:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {str(e)[:80]}"


def is_catch_all(mx_server: str, domain: str) -> bool:
    """
    Tests a provably fake address. If it returns VALID, the domain
    accepts everything — catch-all. No point testing real addresses.
    """
    fake = f"zzznobodyxkq99182@{domain}"
    result = _check_address(mx_server, fake)
    return result == "VALID"


def verify(mx_server: str, email: str, domain: str) -> str:
    """
    Main entry point. Returns VALID, INVALID, CATCH_ALL, UNREACHABLE, or ERROR.
    Runs catch-all detection first to avoid false positives.
    """
    if is_catch_all(mx_server, domain):
        return "CATCH_ALL"
    return _check_address(mx_server, email)

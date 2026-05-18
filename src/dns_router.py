import dns.resolver

def get_mx_server(domain: str) -> str | None:
    try:
        records = dns.resolver.resolve(domain, "MX")
        mx_records = sorted(records, key=lambda r: r.preference)
        return str(mx_records[0].exchange).strip(".")
    except Exception as e:
        print(f"  [-] DNS failed for {domain}: {e}")
        return None

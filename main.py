import json
import csv
import time
from src.dns_router import get_mx_server
from src.permutator import generate_candidates
from src.smtp_verifier import verify


def run_pipeline():
    print("[*] Tamor Contact Agent — starting\n")

    with open("config/targets.json") as f:
        targets = json.load(f)

    results = []

    for t in targets:
        company = t["company"]
        domain = t["domain"]
        first = t["first_name"]
        last = t["last_name"]
        role = t.get("role", "")

        print(f"\n[→] {first} {last} | {role} @ {company} ({domain})")

        mx = get_mx_server(domain)
        if not mx:
            results.append({
                "company": company, "name": f"{first} {last}",
                "role": role, "email": None, "status": "DNS_FAILED"
            })
            continue

        candidates = generate_candidates(first, last, domain)

        found = False
        for candidate in candidates:
            print(f"  [try] {candidate}")
            status = verify(mx, candidate, domain)
            print(f"  [smtp] {status}")

            if status == "VALID":
                print(f"  [✓] {candidate}")
                results.append({
                    "company": company, "name": f"{first} {last}",
                    "role": role, "email": candidate, "status": "VALID"
                })
                found = True
                break

            if status == "CATCH_ALL":
                # domain accepts all — best guess is the top pattern candidate
                print(f"  [~] catch-all domain — logging best guess")
                results.append({
                    "company": company, "name": f"{first} {last}",
                    "role": role, "email": candidates[0], "status": "CATCH_ALL"
                })
                found = True
                break

            if status in ("UNREACHABLE", "TIMEOUT"):
                results.append({
                    "company": company, "name": f"{first} {last}",
                    "role": role, "email": None, "status": status
                })
                found = True
                break

            time.sleep(0.5)

        if not found:
            results.append({
                "company": company, "name": f"{first} {last}",
                "role": role, "email": None, "status": "NOT_FOUND"
            })

    # write outputs
    with open("outputs/results.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "name", "role", "email", "status"])
        writer.writeheader()
        writer.writerows(results)

    with open("outputs/results.json", "w") as f:
        json.dump(results, f, indent=2)

    valid = sum(1 for r in results if r["status"] == "VALID")
    catch_all = sum(1 for r in results if r["status"] == "CATCH_ALL")

    print(f"\n{'='*50}")
    print(f"  Processed  : {len(results)}")
    print(f"  Valid      : {valid}")
    print(f"  Catch-all  : {catch_all}")
    print(f"  Output     : outputs/results.csv")
    print(f"{'='*50}")


if __name__ == "__main__":
    run_pipeline()

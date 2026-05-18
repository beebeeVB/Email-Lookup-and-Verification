import json
import threading
import os
from pathlib import Path
from flask import Flask, render_template, request, jsonify

from src.dns_router import get_mx_server
from src.permutator import generate_candidates
from src.smtp_verifier import verify
from src.domain_finder import find_domain, parse_paste

app = Flask(__name__)

job = {
    "running": False,
    "log": [],
    "results": []
}


def run_job(targets):
    job["running"] = True
    job["log"] = []
    job["results"] = []

    def log(msg):
        job["log"].append(msg)

    for t in targets:
        first = t["first_name"]
        last = t["last_name"]
        company = t["company"]
        domain = t.get("domain") or ""
        role = t.get("role", "")

        # auto-find domain if missing
        if not domain:
            log(f"-> finding domain for {company}...")
            domain = find_domain(company)
            if not domain:
                log(f"  x could not find domain for {company}")
                job["results"].append({
                    "name": f"{first} {last}", "company": company,
                    "role": role, "email": None, "status": "DOMAIN_NOT_FOUND"
                })
                continue
            t["domain"] = domain

        log(f"-> {first} {last} | {role} @ {company} ({domain})")

        mx = get_mx_server(domain)
        if not mx:
            log(f"  x DNS failed for {domain}")
            job["results"].append({
                "name": f"{first} {last}", "company": company,
                "role": role, "email": None, "status": "DNS_FAILED"
            })
            continue

        candidates = generate_candidates(first, last, domain)
        found = False

        for candidate in candidates:
            log(f"  trying {candidate}")
            status = verify(mx, candidate, domain)
            log(f"  smtp -> {status}")

            if status == "VALID":
                log(f"  confirmed: {candidate}")
                job["results"].append({
                    "name": f"{first} {last}", "company": company,
                    "role": role, "email": candidate, "status": "VALID"
                })
                found = True
                break

            if status == "CATCH_ALL":
                log(f"  catch-all domain, best guess: {candidates[0]}")
                job["results"].append({
                    "name": f"{first} {last}", "company": company,
                    "role": role, "email": candidates[0], "status": "CATCH_ALL"
                })
                found = True
                break

            if status in ("UNREACHABLE", "TIMEOUT"):
                job["results"].append({
                    "name": f"{first} {last}", "company": company,
                    "role": role, "email": None, "status": status
                })
                found = True
                break

        if not found:
            job["results"].append({
                "name": f"{first} {last}", "company": company,
                "role": role, "email": None, "status": "NOT_FOUND"
            })

    log("-- done --")
    job["running"] = False

    Path("outputs").mkdir(exist_ok=True)
    with open("outputs/results.json", "w") as f:
        json.dump(job["results"], f, indent=2)


@app.route("/")
def index():
    targets = []
    try:
        with open("config/targets.json") as f:
            targets = json.load(f)
    except Exception:
        pass
    return render_template("index.html", targets=targets)


@app.route("/api/targets", methods=["GET"])
def get_targets():
    try:
        with open("config/targets.json") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify([])


@app.route("/api/targets", methods=["POST"])
def save_targets():
    targets = request.json
    with open("config/targets.json", "w") as f:
        json.dump(targets, f, indent=2)
    return jsonify({"ok": True})


@app.route("/api/parse", methods=["POST"])
def parse():
    """Parse a pasted block of names/companies and return structured targets."""
    text = request.json.get("text", "")
    parsed = parse_paste(text)
    return jsonify(parsed)


@app.route("/api/run", methods=["POST"])
def run():
    if job["running"]:
        return jsonify({"error": "already running"}), 400
    try:
        with open("config/targets.json") as f:
            targets = json.load(f)
    except Exception:
        return jsonify({"error": "no targets"}), 400
    thread = threading.Thread(target=run_job, args=(targets,))
    thread.daemon = True
    thread.start()
    return jsonify({"ok": True})


@app.route("/api/status")
def status():
    return jsonify({
        "running": job["running"],
        "log": job["log"],
        "results": job["results"]
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

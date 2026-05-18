# tamor-contact-agent

A zero-cost email verification agent for B2B market research. No paid APIs. No subscriptions. Finds and verifies corporate email addresses by combining domain pattern detection with direct SMTP handshakes against live mail servers — the same method Hunter.io charges $49/month for.

---

## How It Works

Most email finders guess an address and hope it doesn't bounce. This agent verifies before you ever send. The pipeline runs three steps per target:

```
[Name + Domain] → [Pattern Detection] → [100 Candidate Construction] → [SMTP Handshake] → [Result]
```

### Step 1 — Pattern Detection

The agent scrapes [email-format.com](https://email-format.com) to find the verified email format for the target domain. For example, `amfori.org` uses `{first}.{last}` — so `Mathias Luyten` becomes `mathias.luyten@amfori.org` and that gets tested first.

If the domain isn't indexed on email-format.com, the agent falls back to 100 permutations ranked by global corporate prevalence, organized across 10 tiers:

| Tier | Coverage | Examples |
|---|---|---|
| 1 | ~85% of corporate domains | `first.last`, `flast`, `first_last`, `firstlast` |
| 2 | Less common but widely used | `last.first`, `first-last`, `last_first` |
| 3 | Initial combos | `f_last`, `fi_li`, `lastf`, `last.fi` |
| 4 | Positional variants | `first.last1`, `flast01`, `firstlast1` |
| 5 | Dot and dash combos | `f_first_last`, `last_first_fi`, `fi__last` |
| 6 | Underscore heavy | `first--last`, `fi--last`, `last--fi` |
| 7 | Truncated first name | `fir.last`, `firs.last`, `lastfir` |
| 8 | Truncated last name | `firstlas`, `first.las`, `fi.las` |
| 9 | Numeric collision suffixes | `first.last001`, `flast100`, `firstlast123` |
| 10 | Regional and edge patterns | `info.flast`, `contact.flast`, `first.last.fi` |

The agent stops as soon as one candidate comes back confirmed — it doesn't run all 100 if it finds a match early.

### Step 2 — SMTP Handshake

This is where the verification actually happens. The agent:

1. Looks up the domain's MX record (its mail server address) via DNS
2. Opens a raw TCP connection to that mail server on port 25
3. Sends a `RCPT TO:<candidate@domain.com>` command
4. Reads the server's response code

A `250` response means the mailbox exists and is active. A `550` means it doesn't exist. The agent never actually sends an email — it drops the connection after reading the code.

### Step 3 — Catch-All Detection

Before testing any real address, the agent first tests a provably fake address against the mail server (e.g. `zzznobody99182@domain.com`). If the server returns `250` for that fake address, the domain is configured as **catch-all** — meaning it accepts all incoming mail without revealing which addresses are real. In that case, SMTP verification is unreliable for that domain and the agent flags the result accordingly.

---

## Status Codes

| Status | Meaning | What to do |
|---|---|---|
| `VALID` | SMTP confirmed the mailbox exists. Safe to send. | Send the email |
| `CATCH_ALL` | Server accepts everything. Email is best-guess from pattern. | Send anyway — it won't hard bounce |
| `NOT_FOUND` | All 100 patterns were rejected by the server. | Person may have left, or name/domain is wrong |
| `UNREACHABLE` | Mail server didn't respond or port 25 is blocked. | Run from a different network |
| `DNS_FAILED` | Couldn't resolve the domain's MX record. | Check the domain is correct |

---

## Project Structure

```
tamor-contact-agent/
├── app.py                  # Flask web interface (run this for the UI)
├── main.py                 # CLI pipeline (alternative to the web UI)
├── Procfile                # For Railway deployment
├── requirements.txt
├── config/
│   └── targets.json        # Your input — list of people to find
├── src/
│   ├── dns_router.py       # MX record lookup via dnspython
│   ├── permutator.py       # Pattern scraping + 100 candidate email generation
│   └── smtp_verifier.py    # Direct SMTP handshake engine
├── templates/
│   └── index.html          # Web UI
└── outputs/
    ├── results.csv         # Output after each run
    └── results.json        # Same output in JSON format
```

---

## Setup

### Requirements

- Python 3.10+
- Network access on port 25 (your home/office network — not a cloud server)

### Install

```bash
git clone https://github.com/beebeeVB/Email-verification-AI-agent-.git
cd Email-verification-AI-agent-
pip3 install -r requirements.txt
```

---

## Usage

### Web Interface (recommended)

```bash
python3 app.py
```

Open `http://localhost:5000` in your browser.

The UI lets you:
- Add targets by name, company, domain, and role
- Save targets directly to `config/targets.json`
- Run the agent and watch live logs as it processes each target
- See results in a color-coded table (green = valid, yellow = catch-all, red = failed)

### Command Line

```bash
python3 main.py
```

Reads from `config/targets.json`, prints logs to terminal, saves output to `outputs/`.

---

## Input Format

Edit `config/targets.json` directly or use the web UI to add targets:

```json
[
  {
    "company": "amfori",
    "domain": "amfori.org",
    "first_name": "Mathias",
    "last_name": "Luyten",
    "role": "Head of Digital"
  },
  {
    "company": "Example Corp",
    "domain": "example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "CFO"
  }
]
```

Fields:
- `company` — company name (display only)
- `domain` — bare domain without `www` or `https` (e.g. `amfori.org` not `www.amfori.org`)
- `first_name` — first name exactly as used professionally
- `last_name` — last name
- `role` — job title (display only)

---

## Output Format

Results saved to `outputs/results.csv` and `outputs/results.json` after every run.

| Column | Description |
|---|---|
| `name` | Full name of the target |
| `company` | Company name |
| `role` | Job title |
| `email` | Email address found (or — if not found) |
| `status` | VALID, CATCH_ALL, NOT_FOUND, UNREACHABLE, DNS_FAILED |

---

## Important Constraints

### Port 25 and Network

SMTP verification runs on port 25. Every major cloud platform (Railway, Heroku, Vercel, Render, AWS, GCP) blocks outbound port 25 to prevent spam abuse. Run this locally from your own machine. If you see a lot of `UNREACHABLE` on your home network, your ISP may be blocking port 25 — try your phone's hotspot or a university network.

### Catch-All Domains

Large enterprise companies — especially those using Microsoft 365 or Google Workspace — often configure their mail servers as catch-all. This is a deliberate security configuration. When you see `CATCH_ALL`, the constructed email is still your best option. Send it. It won't hard bounce, and if the pattern is correct it will reach the inbox.

### Name Accuracy

The agent constructs emails from the exact name you provide. Verify the person's professional name on LinkedIn before adding them. If they go by "Bob" not "Robert", use "Bob".

---

## Tips for Better Results

- **Verify names on LinkedIn first.** The tool finds emails, not names. Wrong name = wrong email regardless of verification quality.
- **Check the domain.** Some companies use regional domains for staff emails (e.g. `.fr`, `.de`). Look for email addresses in press releases or the company website.
- **CATCH_ALL is not a failure.** For large enterprise targets it's nearly universal. The constructed email from the verified pattern is accurate — you just don't get SMTP confirmation.
- **NOT_FOUND after 100 patterns** means one of: the person has left, the domain is wrong, or the company uses a non-standard format. Verify on LinkedIn and try again with a corrected name or domain.

---

## Architecture Notes

The SMTP verification approach is identical to what Hunter.io and ZeroBounce sell as a premium feature. The difference is that commercial tools run handshakes from IP addresses with verified PTR records and clean sender reputations, which makes some enterprise mail servers more cooperative. From a residential IP, some servers will refuse the connection at the EHLO stage — hence `UNREACHABLE`.

For market research at tens to low hundreds of contacts, the local approach is sufficient. At 1000+ targets, Hunter.io's API or a dedicated DigitalOcean droplet ($4/month, port 25 permitted) becomes worthwhile.

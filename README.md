# tamor-contact-agent

Finds and verifies corporate email addresses. Zero paid APIs.

## How it works

```
[Domain] → [MX Record] → [Pattern Scrape + Permutations] → [SMTP Handshake] → [results.csv]
```

1. **DNS** — resolves the domain's mail server (MX record)
2. **Pattern** — scrapes email-format.com for the verified format for that domain. Falls back to standard permutations if not indexed.
3. **SMTP** — connects directly to the mail server on port 25, sends `RCPT TO`, reads the response. 250 = real mailbox. No API. Same check Hunter.io charges $49/month for.
4. **Catch-all detection** — tests a fake address first. If the server accepts it, the domain is catch-all and SMTP verification is unreliable.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Input — `config/targets.json`

```json
[
  {
    "company": "Example Corp",
    "domain": "example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "CFO"
  }
]
```

## Output — `outputs/results.csv`

| Field | Values |
|---|---|
| `email` | The address found, or null |
| `status` | `VALID` / `CATCH_ALL` / `NOT_FOUND` / `UNREACHABLE` |

## Notes

- If you get many `UNREACHABLE` results, your IP's port 25 is blocked. Run from a VPS — DigitalOcean $4/month droplet works fine.
- `CATCH_ALL` means the domain's server accepts everything. The email listed is best-guess from the pattern. Send via LinkedIn if you need certainty.

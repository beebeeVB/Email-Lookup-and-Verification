"""
Usage:
  python run.py                        # processes targets/targets.csv
  python run.py --input my_list.csv    # custom input file
"""

import csv
import json
import argparse
from pathlib import Path
from tqdm import tqdm
from agent.pipeline import process

def load_targets(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def save_outputs(results: list[dict]):
    out_dir = Path("outputs")
    out_dir.mkdir(exist_ok=True)

    # JSON
    json_path = out_dir / "results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)

    # CSV
    csv_path = out_dir / "results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    return csv_path, json_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="targets/targets.csv")
    args = parser.parse_args()

    targets = load_targets(args.input)
    print(f"[*] Loaded {len(targets)} targets from {args.input}\n")

    results = []
    for t in tqdm(targets, desc="Processing"):
        result = process(
            name=t["name"],
            company=t["company"],
            domain=t["domain"],
            role=t.get("role", ""),
        )
        results.append(result)

    csv_path, json_path = save_outputs(results)

    valid = [r for r in results if r["status"] == "valid"]
    catch_all = [r for r in results if r["status"] == "catch_all"]
    not_found = [r for r in results if r["status"] == "not_found"]

    print(f"\n{'='*50}")
    print(f"  Total processed : {len(results)}")
    print(f"  Confirmed valid : {len(valid)}")
    print(f"  Catch-all domain: {len(catch_all)}  (email constructed, unverifiable)")
    print(f"  Not found       : {len(not_found)}")
    print(f"\n  Output → {csv_path}")
    print(f"  Output → {json_path}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()

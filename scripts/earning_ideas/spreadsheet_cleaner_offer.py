#!/usr/bin/env python3
"""
Monetizable micro-service starter: Spreadsheet Cleanup + Insights

Offer you can sell:
- "I will clean, normalize, de-duplicate your CSV and deliver an executive summary"

Usage:
  python scripts/earning_ideas/spreadsheet_cleaner_offer.py \
    --in messy.csv --out cleaned.csv --report report.md

No paid APIs required.
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"\D+")


def normalize_header(h: str) -> str:
    h = h.strip().lower()
    h = re.sub(r"[^a-z0-9]+", "_", h)
    return h.strip("_")


def normalize_email(v: str) -> str:
    return v.strip().lower()


def normalize_phone(v: str) -> str:
    digits = PHONE_RE.sub("", v or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    return digits


def score_quality(row: dict[str, str]) -> int:
    score = 0
    if row.get("email") and EMAIL_RE.match(row["email"]):
        score += 1
    if row.get("phone") and len(row["phone"]) >= 10:
        score += 1
    if row.get("name"):
        score += 1
    return score


def dedupe_key(row: dict[str, str]) -> str:
    return row.get("email") or row.get("phone") or row.get("name", "").strip().lower()


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        raw_headers = reader.fieldnames or []
        header_map = {h: normalize_header(h) for h in raw_headers}
        out = []
        for row in reader:
            cleaned = {header_map[k]: (v or "").strip() for k, v in row.items()}
            if "email" in cleaned:
                cleaned["email"] = normalize_email(cleaned["email"])
            if "phone" in cleaned:
                cleaned["phone"] = normalize_phone(cleaned["phone"])
            out.append(cleaned)
        return out


def write_rows(path: Path, rows: list[dict[str, str]]) -> None:
    headers = sorted({k for r in rows for k in r.keys()})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--out", dest="outfile", required=True)
    ap.add_argument("--report", dest="report", required=True)
    args = ap.parse_args()

    in_path = Path(args.infile)
    out_path = Path(args.outfile)
    report_path = Path(args.report)

    rows = load_rows(in_path)
    total_in = len(rows)

    best_by_key: dict[str, dict[str, str]] = {}
    for r in rows:
        k = dedupe_key(r)
        if not k:
            continue
        prev = best_by_key.get(k)
        if prev is None or score_quality(r) > score_quality(prev):
            best_by_key[k] = r

    deduped = list(best_by_key.values())

    invalid_email = sum(1 for r in deduped if r.get("email") and not EMAIL_RE.match(r["email"]))
    missing_name = sum(1 for r in deduped if not r.get("name"))

    domain_counter = Counter()
    for r in deduped:
        em = r.get("email", "")
        if "@" in em and EMAIL_RE.match(em):
            domain_counter[em.split("@", 1)[1]] += 1

    write_rows(out_path, deduped)

    report = f"""# Cleanup Report

- Input rows: **{total_in}**
- Output rows (deduped): **{len(deduped)}**
- Duplicate rows removed: **{total_in - len(deduped)}**
- Rows with invalid email format: **{invalid_email}**
- Rows missing name: **{missing_name}**

## Top email domains
"""

    for domain, count in domain_counter.most_common(10):
        report += f"- {domain}: {count}\n"

    report += """
## Recommended next upsell (manual + automation)
- Add CRM-ready field mapping (HubSpot/Salesforce)
- Build monthly auto-clean pipeline (Zapier/Make + Python)
- Add segmentation tags and follow-up queue export
"""

    report_path.write_text(report, encoding="utf-8")

    print(f"Wrote cleaned CSV: {out_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()

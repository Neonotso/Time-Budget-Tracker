#!/usr/bin/env python3
"""
Opportunity scorecard for overnight triage.

Input: CSV with columns like:
  title,platform,budget,estimated_hours,fit,clarity,category,url

Output:
  - ranked CSV with computed score
  - markdown summary for morning review

Usage:
  python scripts/earning_ideas/opportunity_scorecard.py \
    --in leads.csv --out ranked.csv --report memory/bounty-queue-2026-03-12.md
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def to_float(v: str, default: float = 0.0) -> float:
    try:
        return float((v or "").strip())
    except Exception:
        return default


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def score_row(r: dict[str, str]) -> float:
    # Expected fields from 1-5 scales for fit/clarity.
    budget = to_float(r.get("budget", "0"))
    hours = max(0.5, to_float(r.get("estimated_hours", "2")))
    fit = clamp(to_float(r.get("fit", "3")), 1, 5)
    clarity = clamp(to_float(r.get("clarity", "3")), 1, 5)

    # Higher budget/hour is better; strong weight on fit + clarity for win probability.
    rate = budget / hours
    score = (fit * 2.2) + (clarity * 1.8) + min(6.0, rate / 20.0)

    # Bonus for Ryan's strong lanes.
    txt = " ".join(
        [r.get("title", ""), r.get("category", ""), r.get("platform", "")]
    ).lower()
    bonuses = {
        "automation": 0.8,
        "spreadsheet": 0.7,
        "clip": 0.6,
        "ableton": 0.8,
        "church": 0.7,
        "budget": 0.6,
    }
    for k, b in bonuses.items():
        if k in txt:
            score += b

    return round(score, 2)


def bucket(score: float) -> str:
    if score >= 14:
        return "DO NOW"
    if score >= 11:
        return "INVESTIGATE"
    return "SKIP"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--out", dest="outfile", required=True)
    ap.add_argument("--report", dest="report", required=True)
    args = ap.parse_args()

    in_path = Path(args.infile)
    out_path = Path(args.outfile)
    report_path = Path(args.report)

    with in_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for r in rows:
        s = score_row(r)
        r["score"] = f"{s:.2f}"
        r["bucket"] = bucket(s)

    rows.sort(key=lambda x: float(x["score"]), reverse=True)

    fields = list(rows[0].keys()) if rows else [
        "title",
        "platform",
        "budget",
        "estimated_hours",
        "fit",
        "clarity",
        "category",
        "url",
        "score",
        "bucket",
    ]

    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    top = rows[:10]
    md = ["# Opportunity Queue", "", "Top ranked opportunities:"]
    for i, r in enumerate(top, start=1):
        md.append(
            f"{i}. **{r.get('title','(untitled)')}** — {r.get('platform','?')} | score {r.get('score')} | {r.get('bucket')} | {r.get('url','')}"
        )

    report_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(f"Wrote ranked CSV: {out_path}")
    print(f"Wrote report: {report_path}")


if __name__ == "__main__":
    main()

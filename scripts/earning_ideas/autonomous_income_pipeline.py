#!/usr/bin/env python3
"""
Autonomous no-send overnight income pipeline.

Purpose:
- Take a CSV of opportunities (jobs/bounties/leads)
- Score + rank opportunities by fit and payout efficiency
- Draft tailored proposal snippets WITHOUT sending anything outbound
- Emit morning-ready markdown and JSON artifacts for Ryan review

Usage:
  python scripts/earning_ideas/autonomous_income_pipeline.py \
    --in opportunities.csv \
    --out-md memory/lead-drafts-2026-03-12.md \
    --out-json memory/lead-drafts-2026-03-12.json
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Opportunity:
    title: str
    platform: str
    budget: float
    estimated_hours: float
    fit: float
    clarity: float
    category: str
    url: str
    notes: str = ""


def to_float(v: str, default: float = 0.0) -> float:
    try:
        return float((v or "").strip())
    except Exception:
        return default


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def load_opportunities(path: Path) -> list[Opportunity]:
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        out: list[Opportunity] = []
        for r in reader:
            out.append(
                Opportunity(
                    title=(r.get("title") or "").strip(),
                    platform=(r.get("platform") or "").strip(),
                    budget=to_float(r.get("budget", "0")),
                    estimated_hours=max(0.5, to_float(r.get("estimated_hours", "2"))),
                    fit=clamp(to_float(r.get("fit", "3")), 1, 5),
                    clarity=clamp(to_float(r.get("clarity", "3")), 1, 5),
                    category=(r.get("category") or "").strip(),
                    url=(r.get("url") or "").strip(),
                    notes=(r.get("notes") or "").strip(),
                )
            )
        return out


def compute_score(o: Opportunity) -> float:
    rate = (o.budget / o.estimated_hours) if o.estimated_hours else 0
    score = (o.fit * 2.2) + (o.clarity * 1.8) + min(6.0, rate / 20.0)

    text = f"{o.title} {o.category} {o.platform}".lower()
    for k, b in {
        "automation": 0.8,
        "spreadsheet": 0.7,
        "clip": 0.6,
        "ableton": 0.8,
        "church": 0.7,
        "budget": 0.6,
        "zapier": 0.7,
        "make": 0.6,
    }.items():
        if k in text:
            score += b

    return round(score, 2)


def bucket(score: float) -> str:
    if score >= 14:
        return "DO NOW"
    if score >= 11:
        return "INVESTIGATE"
    return "SKIP"


def proposal_draft(o: Opportunity) -> str:
    return (
        f"Hi — I can help with '{o.title}'. "
        "I specialize in practical automation and cleanup workflows (Sheets/CSV/Zapier/Make), "
        "and can deliver a first pass quickly with clear before/after results. "
        "If you share a sample file/process, I can return a scoped plan + ETA the same day."
    )


def build_records(opps: list[Opportunity]) -> list[dict]:
    records: list[dict] = []
    for o in opps:
        s = compute_score(o)
        records.append(
            {
                **asdict(o),
                "score": s,
                "bucket": bucket(s),
                "proposal_draft": proposal_draft(o),
                "outbound_sent": False,
            }
        )
    records.sort(key=lambda r: r["score"], reverse=True)
    return records


def write_markdown(path: Path, records: list[dict]) -> None:
    lines = [
        "# Overnight Lead Drafts (No Outbound Sent)",
        "",
        "Generated automatically for morning approval.",
        "",
    ]

    top = records[:15]
    for i, r in enumerate(top, 1):
        lines.extend(
            [
                f"## {i}. {r['title']}",
                f"- Platform: {r['platform']}",
                f"- Score: **{r['score']}** ({r['bucket']})",
                f"- Budget / Hours: ${r['budget']} / {r['estimated_hours']}",
                f"- URL: {r['url']}",
                f"- Draft proposal: {r['proposal_draft']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Guardrails",
            "- No applications submitted automatically.",
            "- No messages sent automatically.",
            "- Ryan review required before any outbound action.",
            "",
        ]
    )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-json", required=True)
    args = ap.parse_args()

    opportunities = load_opportunities(Path(args.infile))
    records = build_records(opportunities)

    out_md = Path(args.out_md)
    out_json = Path(args.out_json)

    write_markdown(out_md, records)
    out_json.write_text(json.dumps(records, indent=2), encoding="utf-8")

    print(f"Wrote markdown: {out_md}")
    print(f"Wrote json: {out_json}")


if __name__ == "__main__":
    main()

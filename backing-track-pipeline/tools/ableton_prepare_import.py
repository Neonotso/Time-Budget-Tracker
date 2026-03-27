#!/usr/bin/env python3
"""
Prepare Ableton import artifacts from generated stem metadata.

This script does NOT require Ableton to be running.
It produces a deterministic import plan and optional OSC bootstrap commands.
"""

import argparse
import csv
import json
import re
import socket
import time
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from pythonosc import osc_message_builder, udp_client  # type: ignore
except Exception:
    udp_client = None
    osc_message_builder = None


TRACK_RULES: List[Tuple[re.Pattern, str, str]] = [
    (re.compile(r"drum|kit|perc|percussion|cajon|snare|kick", re.I), "Drums", "Drum Rack"),
    (re.compile(r"bass|contrabass|upright", re.I), "Bass", "Bass Instrument"),
    (re.compile(r"piano|keys|keyboard|rhodes", re.I), "Keys", "Piano/Keys"),
    (re.compile(r"pad|synth|strings|orchestra", re.I), "Pads", "Pad/Strings"),
    (re.compile(r"guitar|acoustic|electric", re.I), "Guitars", "Guitar Instrument"),
    (re.compile(r"lead|vocal|melody|soprano|alto|tenor|baritone", re.I), "Lead", "Lead Instrument"),
    (re.compile(r"click|cue|guide|count", re.I), "Guides", "Click/Cue"),
]


def classify_part(part_name: str) -> Tuple[str, str]:
    for pat, group, hint in TRACK_RULES:
        if pat.search(part_name or ""):
            return group, hint
    return "Other", "General MIDI"


def load_meta(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_plan(meta: Dict) -> Dict:
    rows = []
    for part in meta.get("parts", []):
        name = part.get("name") or f"Part {part.get('index', '')}"
        midi = part.get("midi", "")
        group, hint = classify_part(name)
        rows.append(
            {
                "index": part.get("index"),
                "part_name": name,
                "group": group,
                "instrument_hint": hint,
                "midi": midi,
            }
        )

    group_order = {"Drums": 0, "Bass": 1, "Keys": 2, "Pads": 3, "Guitars": 4, "Lead": 5, "Guides": 6, "Other": 7}
    rows.sort(key=lambda r: (group_order.get(r["group"], 99), (r["part_name"] or "").lower()))

    return {
        "source": meta.get("input"),
        "xml_clean": meta.get("xml_clean"),
        "full_score_midi": meta.get("midi", {}).get("full_score"),
        "tracks": rows,
    }


def write_csv(plan: Dict, out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["index", "group", "part_name", "instrument_hint", "midi"],
        )
        w.writeheader()
        for row in plan["tracks"]:
            w.writerow(row)


class AbletonOSC:
    def __init__(self, host: str = "127.0.0.1", send_port: int = 11000):
        if udp_client is None or osc_message_builder is None:
            raise RuntimeError("python-osc is not installed. Install requirements first.")
        self.client = udp_client.UDPClient(host, send_port)

    def send(self, address: str, *args):
        msg = osc_message_builder.OscMessageBuilder(address=address)
        for arg in args:
            if isinstance(arg, bool):
                msg.add_arg(int(arg), "i")
            elif isinstance(arg, int):
                msg.add_arg(arg, "i")
            elif isinstance(arg, float):
                msg.add_arg(arg, "f")
            else:
                msg.add_arg(str(arg), "s")
        self.client.send(msg.build())
        time.sleep(0.12)


def osc_bootstrap(plan: Dict, host: str, send_port: int, dry_run: bool) -> List[str]:
    commands = []
    track_count = len(plan["tracks"])

    # Build OSC command list first for transparency.
    for i, row in enumerate(plan["tracks"]):
        commands.append(f"/live/song/create_midi_track {i}")
        commands.append(f"/live/track/set/name {i} {row['group']} - {row['part_name']}")

    if dry_run:
        return commands

    osc = AbletonOSC(host=host, send_port=send_port)
    for i, row in enumerate(plan["tracks"]):
        osc.send("/live/song/create_midi_track", i)
        osc.send("/live/track/set/name", i, f"{row['group']} - {row['part_name']}")

    return commands


def main() -> int:
    p = argparse.ArgumentParser(description="Create Ableton import artifacts from stem metadata")
    p.add_argument("--meta", required=True, help="metadata JSON from score_to_midi_stems.py")
    p.add_argument("--plan-out", required=True, help="output import plan JSON")
    p.add_argument("--csv-out", required=True, help="output CSV import sheet")
    p.add_argument("--osc-commands-out", help="optional OSC commands file")
    p.add_argument("--osc-bootstrap", action="store_true", help="send basic track-create/name OSC commands")
    p.add_argument("--dry-run", action="store_true", help="do not send OSC commands")
    p.add_argument("--osc-host", default="127.0.0.1")
    p.add_argument("--osc-send-port", type=int, default=11000)
    args = p.parse_args()

    meta_path = Path(args.meta)
    plan_out = Path(args.plan_out)
    csv_out = Path(args.csv_out)

    meta = load_meta(meta_path)
    plan = build_plan(meta)

    plan_out.parent.mkdir(parents=True, exist_ok=True)
    plan_out.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    write_csv(plan, csv_out)

    if args.osc_bootstrap or args.osc_commands_out:
        commands = osc_bootstrap(plan, args.osc_host, args.osc_send_port, dry_run=(args.dry_run or not args.osc_bootstrap))
        if args.osc_commands_out:
            out = Path(args.osc_commands_out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("\n".join(commands) + "\n", encoding="utf-8")

    print(json.dumps({"plan": str(plan_out), "csv": str(csv_out), "tracks": len(plan['tracks'])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

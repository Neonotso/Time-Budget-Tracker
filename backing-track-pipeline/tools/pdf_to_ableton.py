#!/usr/bin/env python3
"""
One-shot wrapper: PDF -> MusicXML -> MIDI stems -> Ableton import artifacts.

Requires:
- Audiveris CLI reachable via --audiveris-cmd (or in PATH)
- Python deps from requirements.txt
"""

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run(cmd, cwd=None):
    print("$", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def detect_musicxml(xml_raw_dir: Path, stem: str) -> Path:
    candidates = sorted(xml_raw_dir.glob(f"{stem}*.musicxml")) + sorted(xml_raw_dir.glob(f"{stem}*.xml"))
    if not candidates:
        raise FileNotFoundError(
            f"No MusicXML output found in {xml_raw_dir} for stem '{stem}'. "
            "Check Audiveris export output and retry."
        )
    return candidates[0]


def main() -> int:
    p = argparse.ArgumentParser(description="PDF -> MusicXML -> MIDI stems -> Ableton plan")
    p.add_argument("--pdf", required=True, help="Input sheet music PDF")
    p.add_argument("--name", required=True, help="Song slug (e.g. way-maker)")
    p.add_argument("--root", default=".", help="Pipeline root (default: current directory)")
    p.add_argument("--audiveris-cmd", default="audiveris", help="Audiveris CLI command")
    p.add_argument("--skip-omr", action="store_true", help="Skip Audiveris step and use existing xml_raw/<name>.musicxml")
    p.add_argument("--osc-bootstrap", action="store_true", help="Run Ableton OSC track creation/naming step")
    p.add_argument("--osc-host", default="127.0.0.1")
    p.add_argument("--osc-send-port", type=int, default=11000)
    args = p.parse_args()

    root = Path(args.root).resolve()
    pdf = Path(args.pdf).resolve()
    name = args.name.strip()

    input_dir = root / "input"
    xml_raw_dir = root / "xml_raw"
    xml_clean_dir = root / "xml_clean"
    midi_root = root / "midi_stems"
    meta_dir = root / "metadata"
    tools_dir = root / "tools"

    for d in (input_dir, xml_raw_dir, xml_clean_dir, midi_root, meta_dir):
        ensure_dir(d)

    if not pdf.exists():
        raise FileNotFoundError(f"PDF not found: {pdf}")

    staged_pdf = input_dir / f"{name}.pdf"
    if pdf != staged_pdf:
        shutil.copy2(pdf, staged_pdf)
    print(f"Staged PDF: {staged_pdf}")

    if not args.skip_omr:
        if shutil.which(args.audiveris_cmd) is None:
            raise RuntimeError(
                f"Audiveris command not found: {args.audiveris_cmd}. "
                "Install Audiveris or pass --audiveris-cmd with a valid executable path."
            )

        # Typical Audiveris batch/export flow.
        run([
            args.audiveris_cmd,
            "-batch",
            "-export",
            "-output",
            str(xml_raw_dir),
            str(staged_pdf),
        ])

    xml_in = detect_musicxml(xml_raw_dir, name)
    xml_out = xml_clean_dir / f"{name}.clean.musicxml"
    midi_dir = midi_root / name
    meta_out = meta_dir / f"{name}.json"

    run([
        "python3",
        str(tools_dir / "score_to_midi_stems.py"),
        "--input",
        str(xml_in),
        "--xml-out",
        str(xml_out),
        "--midi-dir",
        str(midi_dir),
        "--meta-out",
        str(meta_out),
    ])

    plan_out = meta_dir / f"{name}.ableton-plan.json"
    csv_out = meta_dir / f"{name}.ableton-import.csv"
    osc_txt = meta_dir / f"{name}.osc.txt"

    cmd = [
        "python3",
        str(tools_dir / "ableton_prepare_import.py"),
        "--meta",
        str(meta_out),
        "--plan-out",
        str(plan_out),
        "--csv-out",
        str(csv_out),
        "--osc-commands-out",
        str(osc_txt),
    ]
    if args.osc_bootstrap:
        cmd += [
            "--osc-bootstrap",
            "--osc-host",
            args.osc_host,
            "--osc-send-port",
            str(args.osc_send_port),
        ]

    run(cmd)

    print(json.dumps({
        "pdf": str(staged_pdf),
        "xml_raw": str(xml_in),
        "xml_clean": str(xml_out),
        "midi_dir": str(midi_dir),
        "meta": str(meta_out),
        "plan": str(plan_out),
        "csv": str(csv_out),
        "osc_commands": str(osc_txt),
    }, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

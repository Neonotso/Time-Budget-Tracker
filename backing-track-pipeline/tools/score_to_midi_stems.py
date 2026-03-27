#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from music21 import converter, stream


def safe_name(name: str) -> str:
    keep = []
    for ch in name.strip():
        if ch.isalnum() or ch in ("-", "_"):
            keep.append(ch)
        elif ch in (" ", "/", "\\", ":"):
            keep.append("_")
    out = "".join(keep).strip("_")
    return out or "part"


def write_midi_for_part(part_stream: stream.Part, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    part_stream.write("midi", fp=str(out_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert MusicXML into per-part MIDI stems + metadata")
    parser.add_argument("--input", required=True, help="Input MusicXML path")
    parser.add_argument("--xml-out", required=True, help="Output cleaned MusicXML path")
    parser.add_argument("--midi-dir", required=True, help="Output directory for MIDI stems")
    parser.add_argument("--meta-out", required=True, help="Metadata JSON output path")
    args = parser.parse_args()

    input_path = Path(args.input)
    xml_out = Path(args.xml_out)
    midi_dir = Path(args.midi_dir)
    meta_out = Path(args.meta_out)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    score = converter.parse(str(input_path))

    # Round-trip write for a basic "cleaned" XML output in v1.
    xml_out.parent.mkdir(parents=True, exist_ok=True)
    score.write("musicxml", fp=str(xml_out))

    midi_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "input": str(input_path),
        "xml_clean": str(xml_out),
        "midi": {},
        "parts": [],
    }

    # Full-score MIDI
    full_midi = midi_dir / "00_full_score.mid"
    score.write("midi", fp=str(full_midi))
    outputs["midi"]["full_score"] = str(full_midi)

    # Per-part MIDI stems
    parts = list(score.parts) if hasattr(score, "parts") else []
    seen_names = {}

    for i, p in enumerate(parts, start=1):
        pname = (p.partName or p.id or f"Part_{i}").strip()
        base = safe_name(pname)

        # Handle duplicate part names
        count = seen_names.get(base, 0) + 1
        seen_names[base] = count
        if count > 1:
            base = f"{base}_{count}"

        filename = f"{i:02d}_{base}.mid"
        out_midi = midi_dir / filename
        write_midi_for_part(p, out_midi)

        part_info = {
            "index": i,
            "name": pname,
            "id": p.id,
            "midi": str(out_midi),
        }
        outputs["parts"].append(part_info)

    meta_out.parent.mkdir(parents=True, exist_ok=True)
    meta_out.write_text(json.dumps(outputs, indent=2), encoding="utf-8")

    print(json.dumps(outputs, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

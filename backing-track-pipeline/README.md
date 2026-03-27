# Backing Track Generation Pipeline (v1)

This is a practical first-pass pipeline to convert sheet music into Ableton-ready MIDI stems.

## Goal

Input: score PDF/image

Output:
- cleaned MusicXML
- per-part MIDI stems
- metadata for Ableton import

## Recommended Stack

- OMR: **Audiveris** (PDF/image -> MusicXML)
- Cleanup/export: **music21** + **mido** (Python)
- Optional notation QA: **MuseScore**
- DAW ingest: Ableton Live (manual drag-drop in v1, automation in v2)

## Folder Layout

```text
backing-track-pipeline/
  input/           # source PDFs/images
  xml_raw/         # direct OMR output
  xml_clean/       # cleaned MusicXML
  midi_stems/      # per-part MIDI files
  metadata/        # JSON metadata for downstream automation
  tools/
    score_to_midi_stems.py
    requirements.txt
```

## Install

### 1) Python deps

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r tools/requirements.txt
```

### 2) OMR tool

Install Audiveris (desktop app). Use it to export MusicXML into `xml_raw/`.

### 3) Optional editor

Install MuseScore for quick visual correction of XML files.

## Usage

### One-shot wrapper (recommended)

```bash
python tools/pdf_to_ableton.py \
  --pdf /absolute/path/to/song.pdf \
  --name song
```

This runs:
1. PDF staging into `input/`
2. Audiveris batch export -> `xml_raw/`
3. MusicXML -> MIDI stems + metadata
4. Ableton plan/CSV/OSC command generation

Optional live Ableton OSC bootstrap:

```bash
python tools/pdf_to_ableton.py \
  --pdf /absolute/path/to/song.pdf \
  --name song \
  --osc-bootstrap
```

If you already exported XML manually:

```bash
python tools/pdf_to_ableton.py \
  --pdf /absolute/path/to/song.pdf \
  --name song \
  --skip-omr
```

### Step-by-step (manual)

1. Put score files in `input/`
2. Run OMR (Audiveris) and export MusicXML to `xml_raw/`
3. Convert to stems:

```bash
python tools/score_to_midi_stems.py \
  --input xml_raw/song.musicxml \
  --xml-out xml_clean/song.clean.musicxml \
  --midi-dir midi_stems/song \
  --meta-out metadata/song.json
```

4. Prepare Ableton import plan + optional OSC bootstrap:

```bash
python tools/ableton_prepare_import.py \
  --meta metadata/song.json \
  --plan-out metadata/song.ableton-plan.json \
  --csv-out metadata/song.ableton-import.csv \
  --osc-commands-out metadata/song.osc.txt
```

5. Optional: if AbletonOSC is running, create + name MIDI tracks automatically:

```bash
python tools/ableton_prepare_import.py \
  --meta metadata/song.json \
  --plan-out metadata/song.ableton-plan.json \
  --csv-out metadata/song.ableton-import.csv \
  --osc-bootstrap
```

6. Import generated MIDI stems into those tracks in Ableton.

## v1 Behavior

- Parses score parts from MusicXML
- Writes a cleaned MusicXML copy (round-trip parse/write)
- Exports:
  - full-score MIDI
  - per-part MIDI files
- Writes metadata JSON listing detected parts and output paths

## v2 Behavior (now included)

- Build an **Ableton import plan JSON** with grouped part assignments
- Build a **CSV import sheet** (`group`, `part_name`, `instrument_hint`, `midi path`)
- Optionally output an **OSC command list** for deterministic playback
- Optionally send OSC to Ableton to create and name MIDI tracks

## v3 Upgrades (next)

- Quantization and duration normalization options
- Drum/percussion mapping profiles (e.g., Ableton Drum Rack maps)
- Tempo/time-signature marker extraction for scene creation
- Direct clip import via Max for Live bridge APIs
- Arrangement templates (pads, piano, strings, click, guide cues)

#!/usr/bin/env python3
"""
High-quality quote OCR pipeline for Google Drive folders.

What it does:
- Downloads images from a Drive folder
- Tries multiple rotations + Tesseract modes
- Picks the best OCR pass by confidence
- (Optional) Uses OpenAI vision to clean transcription if OPENAI_API_KEY is set
- Writes a timestamp-ordered text output file

Usage:
  ./venv/bin/python scripts/high_quality_quotes_ocr.py \
    --folder-id 1aFitPWd7kO3CbVA2UA-jOEg2svdZeich \
    --folder-name "War Quotes" \
    --output war_quotes_transcribed_hq.txt

Optional env vars:
  OPENAI_API_KEY=<key>      # enables vision cleanup
  OCR_VISION_MODEL=gpt-4.1-mini
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import os
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

WORKDIR = Path('/Users/ryantaylorvegh/.openclaw/workspace')
ENV_PATH = WORKDIR / '.secrets/google_sheets & drive.env'
TMP_ROOT = WORKDIR / 'tmp_hq_quotes_ocr'


def load_env(path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for raw in path.read_text().splitlines():
        s = raw.strip()
        if not s or s.startswith('#') or '=' not in s:
            continue
        k, v = s.split('=', 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def drive_service():
    env = load_env(ENV_PATH)
    creds = Credentials(
        token=env.get('GOOGLE_SHEETS_ACCESS_TOKEN') or None,
        refresh_token=env.get('GOOGLE_SHEETS_REFRESH_TOKEN'),
        token_uri='https://oauth2.googleapis.com/token',
        client_id=env.get('GOOGLE_SHEETS_CLIENT_ID'),
        client_secret=env.get('GOOGLE_SHEETS_CLIENT_SECRET'),
    )
    if not creds.valid:
        creds.refresh(Request())
    return build('drive', 'v3', credentials=creds)


def list_images(drive, folder_id: str) -> List[dict]:
    q = f"'{folder_id}' in parents and trashed=false and mimeType contains 'image/'"
    files: List[dict] = []
    page = None
    while True:
        resp = drive.files().list(
            q=q,
            fields='nextPageToken, files(id,name,mimeType,createdTime,imageMediaMetadata/time)',
            pageToken=page,
            pageSize=200,
            orderBy='createdTime',
        ).execute()
        files.extend(resp.get('files', []))
        page = resp.get('nextPageToken')
        if not page:
            break
    return files


def download_file(drive, file_id: str, out_path: Path):
    req = drive.files().get_media(fileId=file_id)
    with io.FileIO(out_path, 'wb') as fh:
        dl = MediaIoBaseDownload(fh, req)
        done = False
        while not done:
            _, done = dl.next_chunk()


def tesseract_tsv_text(image_path: Path, psm: int) -> Tuple[str, float]:
    base = image_path.with_suffix(f'.psm{psm}')
    cmd = ['tesseract', str(image_path), str(base), '-l', 'eng', '--psm', str(psm), 'tsv']
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tsv = base.with_suffix('.tsv')
    txt_out = image_path.with_suffix(f'.psm{psm}.txt')
    subprocess.run(['tesseract', str(image_path), str(txt_out.with_suffix('')), '-l', 'eng', '--psm', str(psm)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    text = txt_out.read_text(errors='ignore').strip() if txt_out.exists() else ''
    confs: List[float] = []
    if tsv.exists():
        for line in tsv.read_text(errors='ignore').splitlines()[1:]:
            cols = line.split('\t')
            if len(cols) < 12:
                continue
            try:
                conf = float(cols[10])
            except ValueError:
                continue
            word = cols[11].strip()
            if conf >= 0 and word:
                confs.append(conf)
    mean_conf = sum(confs) / len(confs) if confs else 0.0

    for p in [tsv, txt_out]:
        if p.exists():
            p.unlink()
    return text, mean_conf


def rotate_with_sips(src: Path, angle: int, out_path: Path) -> Path:
    if angle == 0:
        return src
    subprocess.run(['sips', '-r', str(angle), str(src), '--out', str(out_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return out_path if out_path.exists() else src


def best_local_ocr(image_path: Path) -> Tuple[str, int, int, float]:
    # angle, psm search grid
    best = ('', 0, 6, -1.0)
    for angle in (0, 90, 180, 270):
        rotated = image_path.with_suffix(f'.rot{angle}{image_path.suffix}')
        candidate = rotate_with_sips(image_path, angle, rotated)
        for psm in (6, 11, 3):
            text, conf = tesseract_tsv_text(candidate, psm)
            score = conf + min(len(text) / 50.0, 20.0)
            if score > best[3]:
                best = (text, angle, psm, score)
        if rotated.exists():
            rotated.unlink()
    return best


def maybe_vision_cleanup(image_path: Path, rough_text: str) -> str:
    api_key = os.getenv('OPENAI_API_KEY', '').strip()
    if not api_key:
        return rough_text

    model = os.getenv('OCR_VISION_MODEL', 'gpt-4.1-mini')
    b64 = base64.b64encode(image_path.read_bytes()).decode('utf-8')
    prompt = (
        'You are doing OCR transcription from a quote image. '
        'Return only the corrected text content from the image. '
        'No commentary, no markdown. Preserve line breaks where sensible.\n\n'
        'Rough OCR draft (may be noisy):\n'
        f'{rough_text[:4000]}'
    )

    payload = {
        'model': model,
        'input': [
            {
                'role': 'user',
                'content': [
                    {'type': 'input_text', 'text': prompt},
                    {'type': 'input_image', 'image_url': f'data:image/jpeg;base64,{b64}'},
                ],
            }
        ],
    }

    req = urllib.request.Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        text = data.get('output_text', '').strip()
        return text or rough_text
    except Exception:
        return rough_text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--folder-id', required=True)
    ap.add_argument('--folder-name', default='Quotes')
    ap.add_argument('--output', default='quotes_transcribed_hq.txt')
    args = ap.parse_args()

    TMP_ROOT.mkdir(exist_ok=True)
    out_file = WORKDIR / args.output

    drive = drive_service()
    files = list_images(drive, args.folder_id)
    if not files:
        raise SystemExit('No images found in folder')

    items = []
    for f in files:
        fid = f['id']
        safe = ''.join(c for c in f.get('name', fid) if c not in '/\\')
        local = TMP_ROOT / f'{fid}_{safe}'
        if not local.exists():
            download_file(drive, fid, local)

        text, angle, psm, score = best_local_ocr(local)
        text = maybe_vision_cleanup(local, text)

        capture = ((f.get('imageMediaMetadata') or {}).get('time') or '').strip()
        created = f.get('createdTime', '')
        sort_time = capture or created
        items.append({
            'name': f.get('name', fid),
            'capture_time': capture,
            'created_time': created,
            'sort_time': sort_time,
            'angle': angle,
            'psm': psm,
            'score': score,
            'text': text.strip() or '[no text detected]',
        })

    items.sort(key=lambda x: x['sort_time'])

    lines = [
        f"{args.folder_name} — high-quality OCR in timestamp order",
        f"Source folder ID: {args.folder_id}",
        '',
    ]
    for i, it in enumerate(items, start=1):
        lines.append(f"{i}. {it['name']}")
        lines.append(f"   taken: {it['capture_time'] or '[missing in metadata; used Drive created time]'}")
        lines.append(f"   drive_created: {it['created_time']}")
        lines.append(f"   local_ocr: rotation={it['angle']}°, psm={it['psm']}, score={it['score']:.2f}")
        lines.append('   text:')
        for ln in it['text'].splitlines():
            lines.append('   ' + ln)
        lines.append('')

    out_file.write_text('\n'.join(lines) + '\n')
    print(f'WROTE {out_file}')
    print(f'IMAGES {len(items)}')
    if os.getenv('OPENAI_API_KEY', '').strip():
        print('VISION_CLEANUP enabled')
    else:
        print('VISION_CLEANUP disabled (set OPENAI_API_KEY to enable)')


if __name__ == '__main__':
    main()

from pathlib import Path
home = Path.home()
downloads = home / 'Downloads'
rm_dir = downloads / 'reMarkable' / 'Eric'
print('AUDIO_MATCHES')
for p in sorted(downloads.glob('*Eric*')):
    if p.suffix.lower() in {'.m4a', '.mp3', '.wav', '.aiff'}:
        print(str(p))
print('RM_ERIC_DIR_EXISTS', rm_dir.exists())

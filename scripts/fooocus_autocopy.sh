#!/bin/zsh
set -euo pipefail

SRC_ROOT_OUTPUTS="$HOME/.openclaw/workspace/Fooocus/outputs"
SRC_ROOT_TEMP="${TMPDIR%/}/fooocus"
DST_ROOT="$HOME/Downloads/Fooocus"
LOG_FILE="$HOME/.openclaw/workspace/memory/fooocus-autocopy.log"

mkdir -p "$DST_ROOT"
mkdir -p "$(dirname "$LOG_FILE")"

move_tree() {
  local src_root="$1"
  local mode="$2"

  [[ -d "$src_root" ]] || return 0

  # Move only files that are at least ~1 minute old (avoid touching in-progress writes)
  find "$src_root" -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.webp" \) -mmin +0 | while IFS= read -r src; do
    local rel dest dest_dir

    if [[ "$mode" == "outputs" ]]; then
      rel="${src#$src_root/}"
      dest="$DST_ROOT/$rel"
    else
      # Temp files include hashed paths; keep them under _temp to avoid collisions
      rel="${src#$src_root/}"
      dest="$DST_ROOT/_temp/$rel"
    fi

    dest_dir="$(dirname "$dest")"
    mkdir -p "$dest_dir"

    # Move (copy+delete) so source is removed only if transfer succeeds
    if mv "$src" "$dest"; then
      printf "%s moved %s -> %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$src" "$dest" >> "$LOG_FILE"
    fi
  done

  # Clean up empty directories under source root
  find "$src_root" -type d -empty -delete 2>/dev/null || true
}

move_tree "$SRC_ROOT_OUTPUTS" "outputs"
move_tree "$SRC_ROOT_TEMP" "temp"

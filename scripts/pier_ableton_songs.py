#!/usr/bin/env python3
"""
PIER Ableton Songs Setup
========================
Fetches songs from Planning Center and updates Ableton Live scenes with:
- Song names (formatted as: * Song Name "3-word-name")
- Key clips from Pad track
- Tempo clips from Tempo track
"""

import socket
import time
from pythonosc import osc_message_builder, udp_client

# === CONFIG ===
PLANNING_CENTER_TOKEN = "0fc4d60a6aea427337b82c9f5857724b90d2826fd0d77ce465bc97a682e60c5a:pco_pat_04f16a7510f3b48eb90bbb7398d30a15c9b5caae88fcfc40699bb2f6f80a69f10be07d93"
SERVICE_TYPE_ID = "565427"

# Ableton OSC config
OSC_HOST = "localhost"
OSC_SEND_PORT = 11000
OSC_RECV_PORT = 11001

# Track indices (from template exploration)
PAD_TRACK_INDEX = 10
TEMPO_TRACK_INDEX = 11
SAVE_FOLDER = "/Users/ryantaylorvegh/Music/Church/Backing Track Sets"
TEMPLATE_PATH = "/Users/ryantaylorvegh/Music/Ableton/User Library/Templates/Sunday Template for OpenClaw.als"

# Scene indices for songs (0-indexed)
SONG_SCENES = [3, 4, 5, 6, 7]  # 1st through 5th song

# === MULTITRACKS TEMPO LOOKUP ===
# Manual tempo mapping for common songs (BPM)
TEMPO_MAP = {
    "way maker": 68,
    "build my life": 74,
    "shine jesus shine": 78,
    "good god almighty": 68,
    "god i'm just grateful": 74,
    "abide": 72,
    "the narrow way": 70,
    "god, make that fruit grow": 74,
    "yet not i but through christ in me": 72,
    "open up the heavens": 138,
    "abba (arms of a father)": 68,
    "when you walk into the room": 74,
    "pure": 66,
    "open the eyes of my heart": 74,
    "goodbye yesterday": 120,
    "trust in god": 74,
    "who you say i am": 73,
    "the blessing": 68,
}

# === ABLETON OSC CLIENT ===
class AbletonOSC:
    def __init__(self):
        self.client = udp_client.UDPClient(OSC_HOST, OSC_SEND_PORT)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((OSC_HOST, OSC_RECV_PORT))
        self.sock.settimeout(3)
    
    def send(self, address, *args):
        msg = osc_message_builder.OscMessageBuilder(address=address)
        for arg in args:
            if isinstance(arg, int):
                msg.add_arg(arg, 'i')
            elif isinstance(arg, float):
                msg.add_arg(arg, 'f')
            elif isinstance(arg, str):
                msg.add_arg(arg, 's')
        self.client.send(msg.build())
        time.sleep(0.3)  # Increased delay for Ableton to process
    
    def recv(self):
        data, _ = self.sock.recvfrom(4096)
        from pythonosc.osc_message import OscMessage
        m = OscMessage(data)
        return m.params
    
    def set_scene_name(self, scene_index, name):
        """Set scene name"""
        self.send('/live/scene/set/name', scene_index, name)
        print(f"  Set scene {scene_index}: {name}")
    
    def duplicate_clip(self, src_track, src_scene, dst_track, dst_scene):
        """Duplicate a clip from one track/scene to another"""
        self.send('/live/clip_slot/duplicate_clip_to', src_track, src_scene, dst_track, dst_scene)
        print(f"  Duplicated clip: track {src_track} scene {src_scene} -> track {dst_track} scene {dst_scene}")
    
    def get_clip_name(self, track_index, scene_index):
        """Get clip name"""
        self.send('/live/clip/get/name', track_index, scene_index)
        try:
            params = self.recv()
            if len(params) >= 3:
                return params[2]
        except:
            pass
        return None
    
    def set_clip_name(self, track_index, scene_index, name):
        """Set clip name"""
        self.send('/live/clip/set/name', track_index, scene_index, name)
        print(f"  Set clip name: track {track_index} scene {scene_index} = {name}")
    
    def save_set(self, path=None):
        """Save the Live set"""
        # Try the OSC save command
        if path:
            self.send('/live/file/save_as', path)
        else:
            self.send('/live/file/save')
        print(f"  Saving set...")


# === PLANNING CENTER CLIENT ===
import subprocess
import json

class PlanningCenter:
    def __init__(self, token):
        self.token = token
    
    def request(self, endpoint):
        url = f"https://api.planningcenteronline.com/services/v2/{endpoint}"
        cmd = ["curl", "-s", "-u", self.token, url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return json.loads(result.stdout)
    
    def get_plan_date(self, service_type_id, plan_id):
        """Get the date for a specific plan"""
        plan = self.request(f"service_types/{service_type_id}/plans/{plan_id}")
        # Response is wrapped in 'data' key
        data = plan.get("data", {})
        attrs = data.get("attributes", {})
        sort_date = attrs.get("sort_date", "")  # Format: 2026-03-08T10:00:00Z
        return sort_date[:10] if sort_date else None  # Just the date part
    
    def get_upcoming_songs(self, service_type_id, plan_id):
        """Get songs from a specific plan"""
        items = self.request(f"service_types/{service_type_id}/plans/{plan_id}/items")
        songs = []
        for item in items.get("data", []):
            attrs = item.get("attributes", {})
            title = attrs.get("title", "")
            key = attrs.get("key_name") or ""
            item_type = attrs.get("item_type", "")
            
            # Skip non-songs
            if item_type != "song":
                continue
            if "message" in title.lower() or "pre-service" in title.lower() or "benediction" in title.lower() or "greeting" in title.lower():
                continue
            
            songs.append({
                "title": title,
                "key": key
            })
        return songs


# === MAIN ===
def run_for_plan(plan_id):
    print(f"\n=== PIER Ableton Songs Setup - Plan {plan_id} ===\n")
    
    # Fetch plan date for filename
    print("Fetching plan info from Planning Center...")
    pco = PlanningCenter(PLANNING_CENTER_TOKEN)
    plan_date = pco.get_plan_date(SERVICE_TYPE_ID, plan_id)
    print(f"Plan date: {plan_date}")
    
    # Fetch songs from Planning Center
    print("Fetching songs...")
    songs = pco.get_upcoming_songs(SERVICE_TYPE_ID, plan_id)
    print(f"Found {len(songs)} songs")
    for i, song in enumerate(songs):
        print(f"  {i+1}. {song['title']} ({song['key']})")
    
    # Step 1: Copy template PROJECT FOLDER (not just .als file)
    # Get the most recent project folder as template
    dest_path = f"{SAVE_FOLDER}/{plan_date}.als"
    dest_folder = f"{SAVE_FOLDER}/{plan_date} Project"
    
    print(f"\nCreating project folder: {dest_folder}")
    
    # Remove existing destination if present
    if os.path.exists(dest_folder):
        shutil.rmtree(dest_folder)
    
    # Find a template project folder
    existing_folders = [f for f in os.listdir(SAVE_FOLDER) if f.endswith(' Project') and f != f"{plan_date} Project"]
    if existing_folders:
        template_folder = os.path.join(SAVE_FOLDER, existing_folders[0])
        print(f"Using template: {template_folder}")
        
        # Copy entire folder
        shutil.copytree(template_folder, dest_folder)
        
        # Remove old .als file
        old_als_files = [f for f in os.listdir(dest_folder) if f.endswith('.als')]
        for f in old_als_files:
            os.remove(os.path.join(dest_folder, f))
        
        # Copy fresh template .als into project folder
        shutil.copy(TEMPLATE_PATH, os.path.join(dest_folder, f"{plan_date}.als"))
    else:
        # No template folder - create basic structure
        os.makedirs(dest_folder, exist_ok=True)
        os.makedirs(os.path.join(dest_folder, "Ableton Project Info"), exist_ok=True)
        shutil.copy(TEMPLATE_PATH, os.path.join(dest_folder, f"{plan_date}.als"))
    
    print(f"Opening: {dest_path}")
    import subprocess
    subprocess.run(["open", dest_path])
    
    # Wait for Ableton to load
    print("Waiting for Ableton to load...")
    time.sleep(5)
    
    # Step 3: Connect to Ableton
    print("\nConnecting to Ableton...")
    ableton = AbletonOSC()
    
    # Map keys to Pad track scene indices (scenes 22-34 have all 12 keys)
    # Pad track = track 10
    KEY_TO_SCENE = {
        "G": 34, "E": 30, "A": 23, "D": 28,
        "B": 25, "C": 26, "C#": 27, "F": 31, "Ab": 22, "Bb": 24, "Eb": 29,
        "Bm": 25,  # B minor uses B clip (B5 works for both)
    }
    
    # Keys that need minor key lookup (scene -> key name)
    MINOR_KEYS = {
        # Add when found
    }
    
    # Update scenes and copy clips
    print("\nUpdating Ableton...")
    song_titles = []
    tempos = []
    for i, song in enumerate(songs[:5]):  # Max 5 songs
        scene_idx = SONG_SCENES[i]
        song_titles.append(song["title"])
        
        # Format name: * Song Name "3-word-name"
        short_name = " ".join(song["title"].split()[:3])
        scene_name = f'* {song["title"]} "{short_name}"'
        
        ableton.set_scene_name(scene_idx, scene_name)
        
        # Copy key clip from Pad track
        key = song["key"]
        if key in KEY_TO_SCENE:
            src_scene = KEY_TO_SCENE[key]
            if src_scene:
                ableton.duplicate_clip(PAD_TRACK_INDEX, src_scene, PAD_TRACK_INDEX, scene_idx)
        
        # Look up tempo from TEMPO_MAP
        song_lower = song["title"].lower()
        tempo = None
        for name, bpm in TEMPO_MAP.items():
            if name in song_lower:
                tempo = bpm
                break
        
        if tempo:
            tempos.append(tempo)
            print(f"  Song {i+1} '{song['title']}' tempo: {tempo}")
            # Set the tempo clip name in Tempo track
            ableton.set_clip_name(TEMPO_TRACK_INDEX, scene_idx, str(tempo))
        else:
            print(f"  WARNING: No tempo found for '{song['title']}'")
    
    # File is already named correctly (opened from destination folder)
    # Just need to save
    print(f"\nSaving (file already named)...")
    import os
    os.system('osascript -e \'tell application "Live" to activate\' && sleep 0.5 && osascript -e \'tell application "System Events" to tell process "Live" to keystroke "s" using command down\'')
    
    print("\nDone!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: pier_ableton_songs.py <plan_id>")
        print("Example: pier_ableton_songs.py 86270744")
        sys.exit(1)
    
    plan_id = sys.argv[1]
    run_for_plan(plan_id)

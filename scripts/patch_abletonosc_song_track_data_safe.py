#!/usr/bin/env python3
"""Patch AbletonOSC song.py track_data handler to be safe + nested-path aware.

Adds support for nested paths like:
  clip.view.grid_quantization
and avoids request timeouts when a property is missing by returning None.
"""
from pathlib import Path

TARGET = Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC/abletonosc/song.py"

OLD_SNIPPET = '''        def song_get_track_data(params):
            """
            Retrieve one more properties of a block of tracks and their clips.
            Properties must be of the format track.property_name or clip.property_name.

            For example:
                /live/song/get/track_data 0 12 track.name clip.name clip.length

            Queries tracks 0..11, and returns a list of values comprising:

            [track_0_name, clip_0_0_name,   clip_0_1_name,   ... clip_0_7_name,
                           clip_1_0_length, clip_0_1_length, ... clip_0_7_length,
             track_1_name, clip_1_0_name,   clip_1_1_name,   ... clip_1_7_name, ...]
            """
            track_index_min, track_index_max, *properties = params
            track_index_min = int(track_index_min)
            track_index_max = int(track_index_max)
            self.logger.info("Getting track data: %s (tracks %d..%d)" %
                             (properties, track_index_min, track_index_max))
            if track_index_max == -1:
                track_index_max = len(self.song.tracks)
            rv = []
            for track_index in range(track_index_min, track_index_max):
                track = self.song.tracks[track_index]
                for prop in properties:
                    obj, property_name = prop.split(".")
                    if obj == "track":
                        if property_name == "num_devices":
                            value = len(track.devices)
                        else:
                            value = getattr(track, property_name)
                            if isinstance(value, Live.Track.Track):
                                #--------------------------------------------------------------------------------
                                # Map Track objects to their track_index to return via OSC
                                #--------------------------------------------------------------------------------
                                value = list(self.song.tracks).index(value)
                        rv.append(value)
                    elif obj == "clip":
                        for clip_slot in track.clip_slots:
                            if clip_slot.clip is not None:
                                rv.append(getattr(clip_slot.clip, property_name))
                            else:
                                rv.append(None)
                    elif obj == "clip_slot":
                        for clip_slot in track.clip_slots:
                            rv.append(getattr(clip_slot, property_name))
                    elif obj == "device":
                        for device in track.devices:
                            rv.append(getattr(device, property_name))
                    else:
                        self.logger.error("Unknown object identifier in get/track_data: %s" % obj)
            return tuple(rv)
        self.osc_server.add_handler("/live/song/get/track_data", song_get_track_data)
'''

NEW_SNIPPET = '''        def _resolve_attr_path(obj, attr_path: str):
            value = obj
            for part in attr_path.split("."):
                value = getattr(value, part)
            return value

        def _safe_resolve_attr_path(obj, attr_path: str):
            try:
                return _resolve_attr_path(obj, attr_path)
            except Exception as e:
                self.logger.info("track_data: unresolved path %s on %s (%s)" % (attr_path, type(obj), e))
                return None

        def song_get_track_data(params):
            """Safe bulk query of track/clip/clip_slot/device properties.

            Supports nested property paths after the object prefix, for example:
              - clip.name
              - clip.view.grid_quantization
              - track.group_track.name
            """
            track_index_min, track_index_max, *properties = params
            track_index_min = int(track_index_min)
            track_index_max = int(track_index_max)
            self.logger.info("Getting track data: %s (tracks %d..%d)" %
                             (properties, track_index_min, track_index_max))
            if track_index_max == -1:
                track_index_max = len(self.song.tracks)
            rv = []
            for track_index in range(track_index_min, track_index_max):
                track = self.song.tracks[track_index]
                for prop in properties:
                    if "." not in prop:
                        self.logger.error("Invalid property in get/track_data (missing object prefix): %s" % prop)
                        continue
                    obj, property_path = prop.split(".", 1)
                    if obj == "track":
                        if property_path == "num_devices":
                            value = len(track.devices)
                        else:
                            value = _safe_resolve_attr_path(track, property_path)
                            if isinstance(value, Live.Track.Track):
                                try:
                                    value = list(self.song.tracks).index(value)
                                except Exception:
                                    value = None
                        rv.append(value)
                    elif obj == "clip":
                        for clip_slot in track.clip_slots:
                            if clip_slot.clip is not None:
                                rv.append(_safe_resolve_attr_path(clip_slot.clip, property_path))
                            else:
                                rv.append(None)
                    elif obj == "clip_slot":
                        for clip_slot in track.clip_slots:
                            rv.append(_safe_resolve_attr_path(clip_slot, property_path))
                    elif obj == "device":
                        for device in track.devices:
                            rv.append(_safe_resolve_attr_path(device, property_path))
                    else:
                        self.logger.error("Unknown object identifier in get/track_data: %s" % obj)
            return tuple(rv)
        self.osc_server.add_handler("/live/song/get/track_data", song_get_track_data)
'''


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Target not found: {TARGET}")
    text = TARGET.read_text()
    if NEW_SNIPPET in text:
        print("Already patched")
        return
    if OLD_SNIPPET not in text:
        raise SystemExit("Expected old snippet not found; manual merge needed")
    TARGET.write_text(text.replace(OLD_SNIPPET, NEW_SNIPPET))
    print(f"Patched {TARGET}")


if __name__ == "__main__":
    main()

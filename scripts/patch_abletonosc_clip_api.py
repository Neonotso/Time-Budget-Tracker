#!/usr/bin/env python3
"""Patch AbletonOSC clip handler with introspection + clip_view generic access.

This helps discover newly added Live properties (eg Live 12 clip-related features)
without waiting for upstream AbletonOSC releases.
"""
from pathlib import Path

TARGET = Path.home() / "Music/Ableton/User Library/Remote Scripts/AbletonOSC/abletonosc/clip.py"


def main() -> None:
    if not TARGET.exists():
        raise SystemExit(f"Target not found: {TARGET}")

    text = TARGET.read_text()

    if '"root_note",\n            "scale_name",' not in text:
        text = text.replace(
            '"warping",\n        ]',
            '"warping",\n            # Live 12 clip scale/key helpers (availability depends on Live version/API)\n            "root_note",\n            "scale_name",\n        ]'
        )

    if 'def clip_list_available_properties' not in text:
        marker = '        self.osc_server.add_handler("/live/clip/remove/notes", create_clip_callback(clip_remove_notes))\n\n'
        block = '''        def clip_list_available_properties(clip, params: Tuple[Any] = ()):
            # Introspection helper for newer Live versions/features.
            props = []
            for name in dir(clip):
                if name.startswith('_'):
                    continue
                try:
                    value = getattr(clip, name)
                except Exception:
                    continue
                if not callable(value):
                    props.append(name)
            return tuple(sorted(props))

        self.osc_server.add_handler("/live/clip/get/available_properties", create_clip_callback(clip_list_available_properties))

        def clip_view_list_available_properties(clip, params: Tuple[Any] = ()):
            props = []
            view = clip.view
            for name in dir(view):
                if name.startswith('_'):
                    continue
                try:
                    value = getattr(view, name)
                except Exception:
                    continue
                if not callable(value):
                    props.append(name)
            return tuple(sorted(props))

        def clip_view_get_property(clip, params: Tuple[Any] = ()):
            if len(params) < 1:
                raise ValueError("/live/clip_view/get expects a property name")
            prop = str(params[0])
            value = getattr(clip.view, prop)
            if isinstance(value, tuple):
                return (prop, *value)
            return (prop, value)

        def clip_view_set_property(clip, params: Tuple[Any] = ()):
            if len(params) < 2:
                raise ValueError("/live/clip_view/set expects property and value")
            prop = str(params[0])
            value = params[1]
            setattr(clip.view, prop, value)
            return (prop, getattr(clip.view, prop))

        self.osc_server.add_handler("/live/clip_view/get/available_properties", create_clip_callback(clip_view_list_available_properties))
        self.osc_server.add_handler("/live/clip_view/get", create_clip_callback(clip_view_get_property))
        self.osc_server.add_handler("/live/clip_view/set", create_clip_callback(clip_view_set_property))

'''
        if marker in text:
            text = text.replace(marker, marker + block)

    TARGET.write_text(text)
    print(f"Patched {TARGET}")


if __name__ == "__main__":
    main()

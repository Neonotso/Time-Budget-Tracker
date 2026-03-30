{
  "patcher": {
    "fileversion": 1,
    "appversion": {
      "major": 8,
      "minor": 6,
      "revision": 0,
      "architecture": "x64"
    },
    "rect": [
      50.0,
      50.0,
      980.0,
      680.0
    ],
    "boxes": [
      {
        "box": {
          "id": "c0",
          "maxclass": "comment",
          "text": "Ableton Bridge Telemetry (Audio Effect)",
          "patching_rect": [
            30.0,
            20.0,
            320.0,
            20.0
          ]
        }
      },
      {
        "box": {
          "id": "plg",
          "maxclass": "newobj",
          "text": "plugin~",
          "patching_rect": [
            30.0,
            70.0,
            60.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "avg",
          "maxclass": "newobj",
          "text": "average~ 50",
          "patching_rect": [
            30.0,
            110.0,
            90.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "snap",
          "maxclass": "newobj",
          "text": "snapshot~ 20",
          "patching_rect": [
            30.0,
            150.0,
            90.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "js1",
          "maxclass": "newobj",
          "text": "js BridgeTelemetry.js",
          "patching_rect": [
            30.0,
            190.0,
            180.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "prt",
          "maxclass": "newobj",
          "text": "print duck_telemetry",
          "patching_rect": [
            30.0,
            230.0,
            150.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "sym",
          "maxclass": "newobj",
          "text": "tosymbol",
          "patching_rect": [
            200.0,
            230.0,
            70.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "udp",
          "maxclass": "newobj",
          "text": "udpsend 127.0.0.1 8766",
          "patching_rect": [
            280.0,
            230.0,
            170.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "t1",
          "maxclass": "toggle",
          "patching_rect": [
            240.0,
            190.0,
            20.0,
            20.0
          ]
        }
      },
      {
        "box": {
          "id": "i1",
          "maxclass": "number",
          "patching_rect": [
            270.0,
            190.0,
            50.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "c1",
          "maxclass": "comment",
          "text": "manual kick hit (temporary)",
          "patching_rect": [
            330.0,
            190.0,
            180.0,
            20.0
          ]
        }
      },
      {
        "box": {
          "id": "plo",
          "maxclass": "newobj",
          "text": "plugout~",
          "patching_rect": [
            430.0,
            70.0,
            70.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "c2",
          "maxclass": "comment",
          "text": "NOTE: This pass-through keeps Export Max for Live Device enabled.",
          "patching_rect": [
            30.0,
            280.0,
            420.0,
            20.0
          ]
        }
      },
      {
        "box": {
          "id": "n0",
          "maxclass": "comment",
          "text": "ScaleBridge node bridge (global+clip scale commands)",
          "patching_rect": [
            520.0,
            20.0,
            330.0,
            20.0
          ]
        }
      },
      {
        "box": {
          "id": "lb1",
          "maxclass": "newobj",
          "text": "loadbang",
          "patching_rect": [
            520.0,
            50.0,
            60.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "msgp",
          "maxclass": "message",
          "text": "start_poll 500",
          "patching_rect": [
            590.0,
            50.0,
            90.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "nd1",
          "maxclass": "newobj",
          "text": "node.script ScaleBridge.js",
          "patching_rect": [
            520.0,
            85.0,
            180.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "prn",
          "maxclass": "newobj",
          "text": "print scale_bridge",
          "patching_rect": [
            520.0,
            120.0,
            130.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "n1",
          "maxclass": "comment",
          "text": "TODO: route cmd_set_clip_scale / cmd_set_all_clip_scales_from_pad into LiveAPI actions",
          "patching_rect": [
            520.0,
            150.0,
            430.0,
            20.0
          ]
        }
      },
      {
        "box": {
          "id": "mstate",
          "maxclass": "message",
          "text": "state C Minor 1",
          "patching_rect": [
            520.0,
            180.0,
            100.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "mclip",
          "maxclass": "message",
          "text": "clip_state 0 0 C Minor 1",
          "patching_rect": [
            630.0,
            180.0,
            160.0,
            22.0
          ]
        }
      },
      {
        "box": {
          "id": "n2",
          "maxclass": "comment",
          "text": "manual test pushes",
          "patching_rect": [
            800.0,
            180.0,
            120.0,
            20.0
          ]
        }
      }
    ],
    "lines": [
      {
        "patchline": {
          "source": [
            "plg",
            0
          ],
          "destination": [
            "avg",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "avg",
            0
          ],
          "destination": [
            "snap",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "snap",
            0
          ],
          "destination": [
            "js1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "js1",
            0
          ],
          "destination": [
            "prt",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "js1",
            0
          ],
          "destination": [
            "sym",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "sym",
            0
          ],
          "destination": [
            "udp",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "t1",
            0
          ],
          "destination": [
            "i1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "i1",
            0
          ],
          "destination": [
            "js1",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "plg",
            0
          ],
          "destination": [
            "plo",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "plg",
            1
          ],
          "destination": [
            "plo",
            1
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "lb1",
            0
          ],
          "destination": [
            "msgp",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "msgp",
            0
          ],
          "destination": [
            "nd1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "nd1",
            0
          ],
          "destination": [
            "prn",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "mstate",
            0
          ],
          "destination": [
            "nd1",
            0
          ]
        }
      },
      {
        "patchline": {
          "source": [
            "mclip",
            0
          ],
          "destination": [
            "nd1",
            0
          ]
        }
      }
    ]
  }
}
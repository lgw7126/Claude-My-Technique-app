"""M1 analyzer: builds scene records from MP4 structure alone.

Pixel-level analysis (color palette, motion, audio sync) requires a real
decoder and is intentionally left as `None`/pending here. Swap this module
for one backed by ffmpeg + PySceneDetect once the environment has network
access to install them; the DB schema and API already have the fields.
"""
import json

from mp4_probe import build_keyframe_scenes


def analyze_video(filepath):
    """Return (video_meta, scenes) derived from MP4 box structure."""
    result = build_keyframe_scenes(filepath)
    info = result["info"]
    video_track = next((t for t in info["tracks"] if t.get("type") == "vide"), None)

    video_meta = {
        "duration_s": info.get("duration_s"),
        "width": int(video_track["width"]) if video_track else None,
        "height": int(video_track["height"]) if video_track else None,
        "codec": video_track.get("codec") if video_track else None,
        "fps": video_track.get("fps") if video_track else None,
    }

    scenes = []
    for s in result["scenes"]:
        scenes.append({
            "seq": s["seq"],
            "start_ms": s["start_ms"],
            "end_ms": s["end_ms"],
            "sample_count": s["sample_count"],
            "palette": None,  # pending: requires frame decode (ffmpeg)
            "hook_type": None,  # pending: manual tag or rule-based classification
        })

    return video_meta, scenes


def cuts_per_10s(scenes, duration_s):
    if not duration_s:
        return None
    return round(len(scenes) / (duration_s / 10), 2)


def avg_shot_length_ms(scenes):
    if not scenes:
        return None
    lengths = [s["end_ms"] - s["start_ms"] for s in scenes]
    return round(sum(lengths) / len(lengths))

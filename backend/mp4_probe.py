"""Pure-stdlib MP4 (ISO BMFF) box parser.

Extracts duration, resolution, codec, and keyframe sample positions
without any external dependency (no ffmpeg/PyAV required). Used as the
M1 fallback for scene segmentation until a real decoder (ffmpeg +
PySceneDetect) is available in the environment.
"""
import struct


def _iter_boxes(fh, start, end):
    pos = start
    while pos < end - 7:
        fh.seek(pos)
        header = fh.read(8)
        if len(header) < 8:
            break
        size, box_type = struct.unpack(">I4s", header)
        header_size = 8
        if size == 1:
            size = struct.unpack(">Q", fh.read(8))[0]
            header_size = 16
        elif size == 0:
            size = end - pos
        yield box_type.decode("latin1"), pos + header_size, pos + size
        pos += size


_CONTAINER_TYPES = {"moov", "trak", "mdia", "minf", "stbl", "edts", "mvex", "udta"}


def _walk(fh, start, end):
    for box_type, child_start, child_end in _iter_boxes(fh, start, end):
        yield box_type, child_start, child_end
        if box_type in _CONTAINER_TYPES:
            yield from _walk(fh, child_start, child_end)


def probe(path):
    """Return duration, video/audio track info, and keyframe sample indices."""
    with open(path, "rb") as fh:
        file_size = fh.seek(0, 2)
        fh.seek(0)

        info = {"duration_s": None, "tracks": []}
        current = None

        for box_type, start, end in _walk(fh, 0, file_size):
            fh.seek(start)
            if box_type == "mvhd":
                version = fh.read(1)[0]
                fh.seek(start + (20 if version else 12))
                if version:
                    timescale, duration = struct.unpack(">IQ", fh.read(12))
                else:
                    timescale, duration = struct.unpack(">II", fh.read(8))
                info["duration_s"] = duration / timescale if timescale else None

            elif box_type == "trak":
                current = {"samples": 0, "keyframe_sample_ids": []}
                info["tracks"].append(current)

            elif box_type == "tkhd" and current is not None:
                fh.seek(end - 8)
                w, h = struct.unpack(">II", fh.read(8))
                current["width"], current["height"] = w / 65536, h / 65536

            elif box_type == "hdlr" and current is not None:
                fh.seek(start + 8)
                current["type"] = fh.read(4).decode("latin1")

            elif box_type == "mdhd" and current is not None:
                version = fh.read(1)[0]
                fh.seek(start + (20 if version else 12))
                if version:
                    timescale, duration = struct.unpack(">IQ", fh.read(12))
                else:
                    timescale, duration = struct.unpack(">II", fh.read(8))
                current["timescale"] = timescale
                current["duration_s"] = duration / timescale if timescale else None

            elif box_type == "stsd" and current is not None:
                fh.seek(start + 8)
                _, fmt = struct.unpack(">I4s", fh.read(8))
                current["codec"] = fmt.decode("latin1")

            elif box_type == "stts" and current is not None:
                fh.seek(start + 4)
                n = struct.unpack(">I", fh.read(4))[0]
                entries = [struct.unpack(">II", fh.read(8)) for _ in range(n)]
                current["stts_entries"] = entries
                current["samples"] = sum(c for c, _ in entries)
                if entries and current.get("timescale"):
                    common = max(entries, key=lambda e: e[0])
                    current["fps"] = round(current["timescale"] / common[1], 2) if common[1] else None

            elif box_type == "stss" and current is not None:
                fh.seek(start + 4)
                n = struct.unpack(">I", fh.read(4))[0]
                current["keyframe_sample_ids"] = [
                    struct.unpack(">I", fh.read(4))[0] for _ in range(n)
                ]

        return info


def _sample_id_to_seconds(stts_entries, timescale, sample_id):
    """Convert a 1-based sample index into a timestamp using the stts run-length table."""
    remaining = sample_id - 1
    elapsed_ticks = 0
    for count, delta in stts_entries:
        if remaining < count:
            elapsed_ticks += remaining * delta
            return elapsed_ticks / timescale
        remaining -= count
        elapsed_ticks += count * delta
    return elapsed_ticks / timescale


def build_keyframe_scenes(path):
    """Segment a video into scenes using keyframe (sync sample) boundaries.

    This is a structural approximation, not content-based cut detection:
    encoders place keyframes at fixed intervals or on hard scene changes,
    so this is a reasonable stand-in until PySceneDetect is available.
    """
    info = probe(path)
    video_track = next((t for t in info["tracks"] if t.get("type") == "vide"), None)
    if not video_track or not video_track.get("keyframe_sample_ids"):
        return {"info": info, "scenes": []}

    timescale = video_track["timescale"]
    stts_entries = video_track["stts_entries"]
    keyframe_ids = video_track["keyframe_sample_ids"]
    total_samples = video_track["samples"]

    boundaries = keyframe_ids + [total_samples + 1]
    scenes = []
    for i in range(len(keyframe_ids)):
        start_s = _sample_id_to_seconds(stts_entries, timescale, boundaries[i])
        end_s = _sample_id_to_seconds(stts_entries, timescale, boundaries[i + 1])
        scenes.append({
            "seq": i + 1,
            "start_ms": round(start_s * 1000),
            "end_ms": round(end_s * 1000),
            "sample_count": boundaries[i + 1] - boundaries[i],
        })

    return {"info": info, "scenes": scenes}

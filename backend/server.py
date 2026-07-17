"""Technique Studio — M1 backend.

Zero external dependencies: stdlib http.server + sqlite3 only.
Serves the static frontend and a small JSON API on one port.

Run:
    python3 backend/server.py [port]
"""
import cgi
import json
import mimetypes
import re
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db
from analyzer import analyze_video, avg_shot_length_ms, cuts_per_10s

ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"
UPLOAD_DIR = ROOT / "data" / "uploads"
PRESETS_DIR = ROOT / "presets"

ROUTES = []


def route(pattern, methods=("GET",)):
    compiled = re.compile(pattern)

    def decorator(fn):
        ROUTES.append((methods, compiled, fn))
        return fn

    return decorator


@route(r"^/api/presets/(?P<name>[\w-]+)$")
def get_preset(handler, name):
    path = PRESETS_DIR / f"{name}.json"
    if not path.exists():
        return handler.send_json({"error": "preset not found"}, status=404)
    handler.send_json(json.loads(path.read_text(encoding="utf-8")))


@route(r"^/api/videos$", methods=("GET",))
def list_videos(handler):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT id, preset, filename, title, duration_s, width, height, status, created_at "
        "FROM videos ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    handler.send_json([dict(r) for r in rows])


@route(r"^/api/videos/(?P<video_id>\d+)$", methods=("GET",))
def get_video(handler, video_id):
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    conn.close()
    if not row:
        return handler.send_json({"error": "not found"}, status=404)
    handler.send_json(dict(row))


@route(r"^/api/videos/(?P<video_id>\d+)/scenes$", methods=("GET",))
def get_scenes(handler, video_id):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM scenes WHERE video_id = ? ORDER BY seq", (video_id,)
    ).fetchall()
    conn.close()
    scenes = []
    for r in rows:
        d = dict(r)
        d["palette"] = json.loads(d["palette"]) if d["palette"] else None
        scenes.append(d)
    handler.send_json(scenes)


@route(r"^/api/videos/(?P<video_id>\d+)/stats$", methods=("GET",))
def get_stats(handler, video_id):
    conn = db.get_connection()
    video = conn.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if not video:
        conn.close()
        return handler.send_json({"error": "not found"}, status=404)
    scenes = conn.execute(
        "SELECT start_ms, end_ms FROM scenes WHERE video_id = ? ORDER BY seq", (video_id,)
    ).fetchall()
    conn.close()
    scene_list = [dict(s) for s in scenes]
    handler.send_json({
        "cuts_per_10s": cuts_per_10s(scene_list, video["duration_s"]),
        "avg_shot_length_ms": avg_shot_length_ms(scene_list),
        "scene_count": len(scene_list),
    })


@route(r"^/api/upload$", methods=("POST",))
def upload_video(handler):
    content_type = handler.headers.get("Content-Type", "")
    if "multipart/form-data" not in content_type:
        return handler.send_json({"error": "expected multipart/form-data"}, status=400)

    form = cgi.FieldStorage(
        fp=handler.rfile,
        headers=handler.headers,
        environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": content_type},
    )
    if "file" not in form:
        return handler.send_json({"error": "missing file field"}, status=400)

    file_item = form["file"]
    preset = form.getvalue("preset", "viral_grammar")
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    safe_name = re.sub(r"[^\w.\-]", "_", file_item.filename)
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    stored_name = f"{timestamp}_{safe_name}"
    dest_path = UPLOAD_DIR / stored_name
    with open(dest_path, "wb") as out:
        out.write(file_item.file.read())

    try:
        video_meta, scenes = analyze_video(str(dest_path))
    except Exception as exc:
        return handler.send_json({"error": f"analysis failed: {exc}"}, status=500)

    conn = db.get_connection()
    cur = conn.execute(
        "INSERT INTO videos (preset, filename, filepath, title, duration_s, width, height, codec, fps, status) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'analyzed')",
        (
            preset, file_item.filename, str(dest_path.relative_to(ROOT)),
            file_item.filename, video_meta["duration_s"], video_meta["width"],
            video_meta["height"], video_meta["codec"], video_meta["fps"],
        ),
    )
    video_id = cur.lastrowid
    for s in scenes:
        conn.execute(
            "INSERT INTO scenes (video_id, seq, start_ms, end_ms, sample_count, palette, hook_type) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (video_id, s["seq"], s["start_ms"], s["end_ms"], s["sample_count"], None, None),
        )
    conn.commit()
    conn.close()

    handler.send_json({"video_id": video_id, "scene_count": len(scenes)}, status=201)


@route(r"^/api/scenes/(?P<scene_id>\d+)/tag$", methods=("POST",))
def tag_scene(handler, scene_id):
    body = handler.read_json_body()
    tag = (body or {}).get("tag", "").strip()
    if not tag:
        return handler.send_json({"error": "missing tag"}, status=400)
    conn = db.get_connection()
    conn.execute(
        "INSERT INTO tags (scope, target_id, tag) VALUES ('scene', ?, ?)", (scene_id, tag)
    )
    conn.commit()
    conn.close()
    handler.send_json({"ok": True}, status=201)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if not length:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def dispatch(self, method):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path.startswith("/api/"):
            for methods, pattern, fn in ROUTES:
                if method not in methods:
                    continue
                match = pattern.match(path)
                if match:
                    return fn(self, **match.groupdict())
            return self.send_json({"error": "not found"}, status=404)

        if path.startswith("/media/"):
            return self.serve_media(UPLOAD_DIR / Path(path[len("/media/"):]).name)

        if path == "/" or path == "":
            return self.serve_static(FRONTEND_DIR / "index.html")

        return self.serve_static(FRONTEND_DIR / path.lstrip("/"))

    def serve_static(self, filepath: Path):
        if not filepath.is_file():
            return self.send_json({"error": "not found"}, status=404)
        mime, _ = mimetypes.guess_type(str(filepath))
        data = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def serve_media(self, filepath: Path):
        if not filepath.is_file():
            return self.send_json({"error": "not found"}, status=404)
        mime, _ = mimetypes.guess_type(str(filepath))
        file_size = filepath.stat().st_size
        range_header = self.headers.get("Range")

        start, end = 0, file_size - 1
        status = 200
        if range_header:
            match = re.match(r"bytes=(\d*)-(\d*)", range_header)
            if match:
                if match.group(1):
                    start = int(match.group(1))
                if match.group(2):
                    end = int(match.group(2))
                status = 206

        length = end - start + 1
        self.send_response(status)
        self.send_header("Content-Type", mime or "application/octet-stream")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        if status == 206:
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.end_headers()

        if self.command == "HEAD":
            return
        with open(filepath, "rb") as f:
            f.seek(start)
            remaining = length
            chunk_size = 64 * 1024
            while remaining > 0:
                chunk = f.read(min(chunk_size, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)

    def do_GET(self):
        self.dispatch("GET")

    def do_HEAD(self):
        self.dispatch("GET")

    def do_POST(self):
        self.dispatch("POST")

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    db.init_db()
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Technique Studio (M1) running at http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()

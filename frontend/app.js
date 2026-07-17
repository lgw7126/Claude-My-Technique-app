const state = {
  videos: [],
  activeVideoId: null,
  scenes: [],
  activeSceneId: null,
};

const libraryList = document.getElementById("library-list");
const player = document.getElementById("player");
const playerEmpty = document.getElementById("player-empty");
const timeline = document.getElementById("timeline");
const analysisBody = document.getElementById("analysis-body");
const fileInput = document.getElementById("file-input");

function fmtTime(ms) {
  const total = Math.round(ms / 1000);
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

async function loadLibrary() {
  const res = await fetch("/api/videos");
  state.videos = await res.json();
  renderLibrary();
}

function renderLibrary() {
  libraryList.innerHTML = "";
  if (state.videos.length === 0) {
    libraryList.innerHTML = '<div class="empty-state">아직 업로드된 영상이 없습니다</div>';
    return;
  }
  for (const v of state.videos) {
    const el = document.createElement("div");
    el.className = "library-item" + (v.id === state.activeVideoId ? " active" : "");
    const dur = v.duration_s ? `${Math.round(v.duration_s)}s` : "-";
    el.innerHTML = `<div class="title">${v.title || v.filename}</div>
      <div class="meta">${v.width || "?"}×${v.height || "?"} · ${dur} · ${v.status}</div>`;
    el.addEventListener("click", () => selectVideo(v.id));
    libraryList.appendChild(el);
  }
}

async function selectVideo(id) {
  state.activeVideoId = id;
  renderLibrary();

  const [videoRes, scenesRes] = await Promise.all([
    fetch(`/api/videos/${id}`),
    fetch(`/api/videos/${id}/scenes`),
  ]);
  const video = await videoRes.json();
  state.scenes = await scenesRes.json();

  player.src = `/media/${video.filepath.split("/").pop()}`;
  player.style.display = "block";
  playerEmpty.style.display = "none";

  renderTimeline();
  analysisBody.innerHTML = '<div class="empty-state">장면을 선택하면 분석 결과가 표시됩니다</div>';
}

function renderTimeline() {
  timeline.innerHTML = "";
  for (const s of state.scenes) {
    const el = document.createElement("div");
    el.className = "scene-thumb" + (s.id === state.activeSceneId ? " active" : "");
    el.innerHTML = `<div class="seq">#${s.seq}</div><div>${fmtTime(s.start_ms)}</div>`;
    el.addEventListener("click", () => selectScene(s));
    timeline.appendChild(el);
  }
}

function selectScene(scene) {
  state.activeSceneId = scene.id;
  renderTimeline();
  player.currentTime = scene.start_ms / 1000;

  const durationMs = scene.end_ms - scene.start_ms;
  const paletteHtml = scene.palette
    ? `<div class="palette-swatches">${scene.palette
        .map((hex) => `<div class="swatch" style="background:${hex}"></div>`)
        .join("")}</div>`
    : `<div class="pending">색상 분석 대기 중 — ffmpeg 설치 후 자동 산출됩니다</div>`;

  analysisBody.innerHTML = `
    <div class="card">
      <div class="label">장면 #${scene.seq}</div>
      <div class="value">${fmtTime(scene.start_ms)} – ${fmtTime(scene.end_ms)} (${durationMs}ms)</div>
    </div>
    <div class="card">
      <div class="label">컬러 팔레트</div>
      ${paletteHtml}
    </div>
    <div class="card">
      <div class="label">훅 유형</div>
      <div class="pending">미분류 — 태그로 직접 지정하세요</div>
    </div>
    <div class="card">
      <div class="label">태그 추가</div>
      <input class="tag-input" id="tag-input" placeholder="예: 얼굴 클로즈업 훅" />
    </div>
  `;

  document.getElementById("tag-input").addEventListener("keydown", async (e) => {
    if (e.key !== "Enter" || !e.target.value.trim()) return;
    await fetch(`/api/scenes/${scene.id}/tag`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tag: e.target.value.trim() }),
    });
    e.target.value = "";
  });
}

fileInput.addEventListener("change", async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("preset", "viral_grammar");

  libraryList.innerHTML = '<div class="empty-state">분석 중…</div>';
  const res = await fetch("/api/upload", { method: "POST", body: formData });
  const result = await res.json();
  if (result.error) {
    alert("분석 실패: " + result.error);
  }
  await loadLibrary();
  if (result.video_id) selectVideo(result.video_id);
  fileInput.value = "";
});

loadLibrary();

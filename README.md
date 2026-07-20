# 🎬 Technique Studio (Claude-My-Technique-app)

> **▶ 가장 빠른 실행:** `standalone/index.html`을 브라우저로 열면 끝. 설치·서버 불필요.
> **▶ 전체 기능 실행:** `python3 backend/server.py 8000` → http://localhost:8000

영상을 장면 단위로 자동 분해하고 연출 기법을 분석해 레퍼런스 라이브러리로 축적하는 로컬 웹앱.

## 제작 의도

레퍼런스 영상을 볼 때 "이 컷이 왜 좋은지"는 대충 알겠는데, 그걸 언어로 정리해
나중에 다시 찾아 쓸 수 있게 남기는 일은 거의 하지 않게 된다. 결국 매번 처음부터 다시 본다.

Technique Studio는 **영상을 넣으면 장면 단위로 잘라서 컷 빈도·샷 길이 같은 수치를 뽑고,
거기에 내가 태그를 달아 축적하는 개인용 레퍼런스 라이브러리**다.
외부 서비스에 올리지 않고 내 컴퓨터 안에서만 돌아간다.

## 두 가지 실행 방식

| | standalone (브라우저 단독) | backend (Python 서버) |
|---|---|---|
| 실행 | `standalone/index.html` 더블클릭 | `python3 backend/server.py 8000` |
| 설치 | 없음 | 없음 (Python 표준 라이브러리만) |
| 데이터 저장 | 브라우저 안에만 | 로컬 DB에 축적 |
| 용도 | 빠르게 한 편 분석해보기 | 라이브러리로 쌓아가기 |

`web/index.html`은 standalone과 동일한 최신 화면이다.

## 사용법

1. **영상 추가** — "+ 영상 추가"로 mp4 업로드 (또는 `standalone/samples/`의 샘플 사용)
2. **자동 장면 분할** — MP4 키프레임 경계를 읽어 컷을 나눈다 (ffmpeg 불필요)
3. **타임라인 확인** — 가운데 패널에서 컷별 재생, 오른쪽에 분석 결과
4. **태그 달기** — 훅 유형·연출 기법 등 내 기준으로 분류
5. **통계 확인** — 컷 빈도, 평균 샷 길이 등으로 영상 간 비교

### 영상 수집 도구 (Windows)

`standalone/쇼츠받기.hta`를 더블클릭하면 URL을 붙여넣어 쇼츠를 내려받을 수 있다.
`yt-dlp.exe`가 같은 폴더에 있어야 동작한다 ([공식 배포처](https://github.com/yt-dlp/yt-dlp/releases)에서 받아 저장소 루트에 두면 된다 — 용량 문제로 저장소에는 포함하지 않음).

## 현재 상태

- ✅ 3단 레이아웃 UI (라이브러리 / 플레이어+타임라인 / 분석 패널)
- ✅ MP4 구조 기반 장면 분할 (키프레임 경계, ffmpeg 불필요)
- ✅ 태그 지정, 컷 빈도·평균 샷 길이 통계
- ✅ 라이브러리 검색·정렬·인사이트·내보내기 (M4)
- ✅ standalone 브라우저 단독 버전 + 트렌딩 모달
- ⏳ 컬러 팔레트 / 오디오 싱크 / 훅 자동 분류 — ffmpeg + PySceneDetect 설치 후 활성화 예정
- ⏳ 트렌딩 자동 수집 (YouTube Data API) — M3

## 폴더 구조

```
backend/     Python 서버 (server.py, analyzer.py, mp4_probe.py, db.py)
frontend/    서버 모드 프론트엔드
web/         standalone 화면 (최신)
standalone/  브라우저 단독 실행 버전 + 쇼츠 수집 도구 + 샘플 영상
presets/     분석 프리셋 (viral_grammar.json)
docs/        PRD.md, HANDOFF.md
```

## 문서

설계 배경과 전체 로드맵은 [`docs/PRD.md`](docs/PRD.md) 참고.

---

작성: GO_NY × Claude

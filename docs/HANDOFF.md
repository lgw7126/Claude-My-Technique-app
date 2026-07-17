# 인수인계 문서 (HANDOFF)

새 세션에서 이 문서와 `docs/PRD.md`를 먼저 읽으면 전체 맥락을 파악할 수 있다.

- **최종 업데이트**: 2026-07-17
- **작업 브랜치**: `claude/image-video-analysis-wq8xby`

## 1. 프로젝트가 뭔가

영상을 장면 단위로 자동 분해하고 연출 기법(컷 리듬·컬러·훅)을 분석해 레퍼런스
라이브러리로 축적하는 앱. 사용자가 Threads에서 본 "MV Technique Studio" 스타일을
**주제만 바꿔** 재해석한 것. 상세 설계는 `docs/PRD.md` (반드시 읽을 것).

- 구조: 공통 코어 + 주제 프리셋 2개
- 파일럿 주제(우선 구현): **Viral Grammar** — 트렌딩 쇼츠의 편집 문법 분석
- 2차 주제: **Runway Studio** — 패션쇼/룩북 분석 (스키마 교체만으로 추가)

## 2. 사용자가 결정한 것들

- ✅ 코어 1개 + 프리셋 2개 구조 승인, 파일럿은 Viral Grammar
- ✅ **전자동 파이프라인 필수** — "일일이 업로드"는 거부. 트렌딩 수집(YouTube Data API)
  → 자동 다운로드(yt-dlp, 개인용) → 로컬 분석 → 원본 삭제·리포트만 보관
- ✅ 자동 다운로드의 약관 위반 소지 인지하고 수용 (개인용). `fetch_mode: auto|upload`
  스위치로 격리해 공개 배포 시 upload 모드 전환
- ⬜ 미결정 (PRD 7절): 앱 이름 확정, 수집 국가/개수, 스케줄 시각, v2 Claude API 채택

## 3. 지금까지 만든 것 (모두 이 브랜치에 커밋됨)

| 경로 | 내용 | 상태 |
|------|------|------|
| `docs/PRD.md` | 전체 제품 설계 문서 | 완료 |
| `backend/` | 의존성 제로 M1 서버 (stdlib http.server + sqlite3). 업로드→MP4 구조 파싱→장면 분할→통계 API. Range 재생 지원 | 완료·동작 검증됨 |
| `backend/mp4_probe.py` | 순수 Python MP4 박스 파서 — ffmpeg 없이 키프레임(stss) 경계로 장면 분할 | 완료 |
| `frontend/` | 3단 레이아웃 웹 UI (서버용) | 완료 |
| `web/index.html` | **단일 파일 스탠드얼론 버전** — 서버·설치 없이 브라우저만으로 동작. JS로 MP4 파싱, Canvas로 실제 프레임 썸네일·k-means 팔레트·프레임diff 정밀 컷 감지·첫1초 훅 지표, localStorage 저장 | 완료·파서 검증됨 |
| `presets/viral_grammar.json` | 파일럿 주제 분석 스키마 | 완료 |

검증된 사실: 샘플 영상(69.5s, 2252×1044, H.264)에서 Python·JS 파서 모두 동일하게
9개 장면 산출. 서버 버전은 업로드→분석→타임라인→태그까지 e2e 확인.

## 4. 환경 제약 (중요 — 시간 낭비 방지)

- **이전 세션의 네트워크 정책은 pypi/npm/apt 전부 403이었다.** 사용자가 환경 설정에서
  Network access를 상향했다고 하니, 새 세션에서는 먼저 `pip install pyscenedetect` 등이
  되는지 확인할 것. 안 되면 M1 방식(의존성 제로)으로 계속 우회.
- 이 저장소의 클라우드 세션은 사용자 브라우저에서 `localhost` 접속 불가.
  **사용자는 비개발자** — git clone/python 실행 안내는 실패했음. 사용자에게 보여줄 때는
  ① `web/index.html` 단일 파일을 쓰거나(파일 하나 저장해 더블클릭) ② 스크린샷으로 시연.
- 샌드박스 Chromium/Playwright ffmpeg에는 H.264 코덱이 없어 **샌드박스 안에서는
  프레임 디코딩 불가**. `web/index.html`의 픽셀 분석은 사용자의 실제 Chrome에서만 검증
  가능 (파서 로직은 샌드박스에서 검증 완료).
- GitHub 쓰기 권한이 한동안 403이었다가 복구됨. 푸시 실패 시 사용자에게
  github.com/settings/installations 에서 Claude 앱 권한 확인 요청.
- main 브랜치에 사용자가 올린 샘플 파일 2개(스크린샷 png, 녹음 mp4)가 있음.
  이 브랜치에는 없으니 필요하면 `git show origin/main:"<파일명>"` 으로 꺼낼 것.

## 5. 다음 할 일 (우선순위 순)

1. **사용자에게 앱 보여주기**: `web/index.html`을 SendUserFile로 전달하거나 아티팩트로
   게시 (직전 세션에서 아티팩트 게시를 사용자가 한 번 거부했음 — 의사 먼저 확인).
2. **M2 — 분석 정밀화**: 네트워크가 열렸으면 ffmpeg + PySceneDetect 설치 후
   `backend/analyzer.py` 교체 (구조는 교체 전제로 설계돼 있음). 오디오 싱크 점수,
   자막 영역 감지 추가.
3. **M3 — 전자동 파이프라인**: YouTube Data API 수집기(사용자 API 키 발급 안내 필요),
   yt-dlp Fetcher(`fetch_mode` 스위치), 정리기(원본 삭제), 스케줄러.
4. **M4 — 라이브러리 UX**: 검색/필터/정렬/태그 모아보기.
5. **M5 — Runway 프리셋**: `presets/runway_studio.json` 추가 + 주제 스위처 활성화.

## 6. 실행 방법

```bash
# 서버 버전 (개발 환경에서)
python3 backend/server.py 8000

# 스탠드얼론 버전 (사용자에게)
web/index.html 파일을 브라우저에서 열기 — 그게 전부
```

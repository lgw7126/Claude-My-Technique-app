# Claude-My-Technique-app

영상을 장면 단위로 자동 분해하고 연출 기법을 분석해 레퍼런스 라이브러리로 축적하는 로컬 웹앱.
설계 배경과 전체 로드맵은 [`docs/PRD.md`](docs/PRD.md) 참고.

## 실행 방법 (M1)

외부 패키지 설치 없이 Python 표준 라이브러리만으로 동작합니다.

```bash
python3 backend/server.py 8000
```

브라우저에서 `http://localhost:8000` 접속 후 "+ 영상 추가"로 mp4 파일을 업로드하면
장면 타임라인이 자동 생성됩니다.

## 현재 상태

- ✅ 3단 레이아웃 UI (라이브러리 / 플레이어+타임라인 / 분석 패널)
- ✅ MP4 구조 기반 장면 분할 (키프레임 경계, ffmpeg 불필요)
- ✅ 태그 지정, 컷 빈도·평균 샷 길이 통계
- ⏳ 컬러 팔레트 / 오디오 싱크 / 훅 자동 분류 — ffmpeg + PySceneDetect 설치 후 활성화 예정
- ⏳ 트렌딩 자동 수집 (YouTube Data API) — M3

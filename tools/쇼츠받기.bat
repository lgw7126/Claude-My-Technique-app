@echo off
chcp 65001 >nul
title 쇼츠 다운로드 도우미 - Technique Studio

if not exist "%~dp0yt-dlp.exe" (
  echo.
  echo  [준비 필요 - 처음 한 번만]
  echo  yt-dlp.exe 파일이 이 폴더에 없습니다.
  echo  브라우저에서 아래 주소를 열면 바로 내려받아집니다:
  echo.
  echo    https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe
  echo.
  echo  내려받은 yt-dlp.exe 를 이 파일과 같은 폴더에 넣고 다시 실행하세요.
  echo.
  pause
  exit /b
)

echo.
echo  ── Technique Studio 쇼츠 다운로드 ──────────────
echo   유튜브 링크를 붙여넣으면 '쇼츠' 폴더에 mp4로 저장됩니다.
echo   저장된 파일을 앱의 [+ 영상 추가]에 넣으면 분석 시작.
echo  ────────────────────────────────────────────────
echo.

:loop
set "URL="
set /p URL= 쇼츠 링크 붙여넣고 Enter (그냥 Enter = 종료):
if "%URL%"=="" exit /b

"%~dp0yt-dlp.exe" --no-playlist -P "%~dp0쇼츠" -o "%%(title).60s.%%(ext)s" -f "b[ext=mp4]/b" "%URL%"
echo.
echo  [완료] '쇼츠' 폴더를 확인하세요.
echo.
goto loop

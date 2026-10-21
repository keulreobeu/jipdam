#!/bin/zsh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
APP="$ROOT/outputs/budongi_mvp_temp"
VENV="$ROOT/.local_runtime/mac-launcher/venv"

if [[ ! -f "$APP/src/budongi/cli.py" ]]; then
  echo "집담 프로젝트 폴더를 찾을 수 없습니다. 저장소 최상단에서 실행해 주세요."
  read -r "?Enter를 누르면 종료합니다."
  exit 1
fi

PYTHON=""
for candidate in python3; do
  if command -v "$candidate" >/dev/null 2>&1; then
    PYTHON="$(command -v "$candidate")"
    break
  fi
done
if [[ -z "$PYTHON" ]]; then
  echo "Python 3.11 이상을 설치한 뒤 다시 실행해 주세요."
  read -r "?Enter를 누르면 종료합니다."
  exit 1
fi
if ! "$PYTHON" -c 'import sys; raise SystemExit(sys.version_info < (3, 11))'; then
  echo "Python 3.11 이상이 필요합니다."
  read -r "?Enter를 누르면 종료합니다."
  exit 1
fi

if [[ ! -x "$VENV/bin/python" ]]; then
  mkdir -p "$(dirname "$VENV")"
  "$PYTHON" -m venv "$VENV"
fi
if ! "$VENV/bin/python" -c 'import cryptography, openpyxl, keyring' >/dev/null 2>&1; then
  echo "집담 실행에 필요한 라이브러리를 준비합니다."
  "$VENV/bin/python" -m pip install --disable-pip-version-check -e "$APP"
fi

cd "$APP"
echo ""
echo "집담 실행 메뉴"
echo "1) 전월세 서버"
echo "2) API 키 보관함"
echo "q) 종료"
read -r "?선택: " choice
case "$choice" in
  1) "$VENV/bin/python" "$ROOT/server_launcher.py" ;;
  2) "$VENV/bin/python" "$ROOT/credential_launcher.py" ;;
  q|Q) exit 0 ;;
  *) echo "메뉴에서 다시 선택해 주세요."; exit 2 ;;
esac
echo ""
read -r "?서버를 종료하려면 Enter를 누르세요."

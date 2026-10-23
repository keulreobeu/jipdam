"""Windows bootstrapper for the local Jipdam rental MVP server."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

LAUNCH_DIR = Path(sys.executable if getattr(sys, "frozen", False) else __file__).resolve().parent
DEFAULT_PORT = 8766
PORT_RANGE = range(8766, 8797)
URL_TEMPLATE = "http://127.0.0.1:{port}/"


def _find_app_dir() -> Path | None:
    anchors = [LAUNCH_DIR, Path.cwd()]
    candidates: list[Path] = []
    for anchor in anchors:
        candidates.extend((anchor, anchor / "outputs" / "budongi_mvp_temp"))
    for parent in LAUNCH_DIR.parents:
        candidates.append(parent / "outputs" / "budongi_mvp_temp")
    seen: set[Path] = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        if (candidate / "src" / "budongi" / "cli.py").is_file():
            return candidate
    return None


def _database(app_dir: Path) -> Path:
    return app_dir / "data" / "rental" / "serving" / "reviewed-20261020.sqlite3"


def _show_error(message: str) -> None:
    if getattr(sys, "frozen", False) and os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, message, "집담 서버 실행", 0x10)
    else:
        print(message)


def _ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(URL_TEMPLATE.format(port=port) + "api/status", timeout=1) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def _choose_port() -> int | None:
    for port in PORT_RANGE:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            probe.bind(("127.0.0.1", port))
            return port
        except OSError:
            continue
        finally:
            probe.close()
    return None


def main() -> int:
    app_dir = _find_app_dir()
    if app_dir is None:
        _show_error("집담 앱 폴더를 찾을 수 없습니다. 저장소 루트 또는 outputs/budongi_mvp_temp에서 실행해 주세요.")
        return 1
    database = _database(app_dir)
    if not database.is_file():
        _show_error(f"전월세 데이터베이스를 찾을 수 없습니다.\n{database}")
        return 1

    port = DEFAULT_PORT if _ready(DEFAULT_PORT) else _choose_port()
    if port is None:
        _show_error("8766~8796 포트를 사용할 수 없습니다. 다른 서버를 종료한 뒤 다시 실행해 주세요.")
        return 1
    if not _ready(port):
        python = shutil.which("python") or shutil.which("py")
        if not python:
            _show_error("Python 3.11 이상을 찾을 수 없습니다. Python을 설치한 뒤 다시 실행해 주세요.")
            return 1
        command = [python, "-X", "utf8", "-m", "budongi.cli",
                   "rental-mvp", "--database", str(database), "--no-browser", "--port", str(port)]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(app_dir / "src")
        try:
            print(f"집담 서버를 시작합니다: {URL_TEMPLATE.format(port=port)}", flush=True)
            subprocess.Popen(command, cwd=app_dir, env=env,
                             stdin=subprocess.DEVNULL, close_fds=True)
        except OSError as exc:
            _show_error(f"서버를 시작하지 못했습니다: {exc}")
            return 1

        for _ in range(60):
            if _ready(port):
                break
            time.sleep(0.5)
        else:
            _show_error("서버 시작을 확인하지 못했습니다. 위 터미널의 오류를 확인해 주세요.")
            return 1

    url = URL_TEMPLATE.format(port=port)
    print(f"서버 준비 완료. 브라우저를 엽니다: {url}", flush=True)
    webbrowser.open(url, new=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

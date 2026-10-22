"""Cross-platform console launcher for the local encrypted API credential vault."""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

from server_launcher import URL_TEMPLATE, _find_app_dir


def _ready(port: int) -> bool:
    try:
        with urllib.request.urlopen(URL_TEMPLATE.format(port=port), timeout=1) as response:
            return response.status == 200
    except (OSError, urllib.error.URLError):
        return False


def main() -> int:
    if getattr(sys, "frozen", False) and len(sys.argv) > 1 and sys.argv[1] == "--jipdam-child":
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        from budongi.cli import main as cli_main
        cli_main()
        return 0
    app_dir = _find_app_dir()
    if app_dir is None:
        print("집담 앱 폴더를 찾을 수 없습니다. 저장소 루트 또는 outputs/budongi_mvp_temp에서 실행하세요.")
        input("Enter 키를 누르면 닫힙니다.")
        return 1

    port = 8765
    if not _ready(port):
        # API-key vault keeps its historical default port 8765; on conflict, use
        # an unused port from the same bounded local range.
        port = next((p for p in range(8765, 8797) if _choose_specific_port(p)), None)
        if port is None:
            print("8765~8796 포트를 사용할 수 없습니다. 다른 서버를 종료해 주세요.")
            input("Enter 키를 누르면 닫힙니다.")
            return 1
        if getattr(sys, "frozen", False):
            command = [sys.executable, "--jipdam-child", "credentials", "--port", str(port), "--no-browser"]
        else:
            python = sys.executable
            command = [python, "-X", "utf8", "-m", "budongi.cli", "credentials",
                       "--port", str(port), "--no-browser"]
        import os
        env = os.environ.copy()
        env["PYTHONPATH"] = str(app_dir / "src")
        try:
            print(f"API 키 보관함 서버를 시작합니다: {URL_TEMPLATE.format(port=port)}", flush=True)
            subprocess.Popen(command, cwd=app_dir, env=env, stdin=subprocess.DEVNULL, close_fds=True)
        except OSError as exc:
            print(f"서버 시작 실패: {exc}")
            input("Enter 키를 누르면 닫힙니다.")
            return 1
        for _ in range(60):
            if _ready(port):
                break
            time.sleep(0.5)
        else:
            print("보관함 서버 시작을 확인하지 못했습니다. 위 터미널의 오류를 확인해 주세요.")
            input("Enter 키를 누르면 닫힙니다.")
            return 1

    url = URL_TEMPLATE.format(port=port)
    print(f"보관함 서버 준비 완료: {url}", flush=True)
    webbrowser.open(url, new=2)
    return 0


def _choose_specific_port(port: int) -> bool:
    import socket
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        probe.close()


if __name__ == "__main__":
    raise SystemExit(main())

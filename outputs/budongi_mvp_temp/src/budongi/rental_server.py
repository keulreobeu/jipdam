"""Loopback web app for private rental intake and evidence-based comparison."""
from __future__ import annotations

import json
import math
import os
import secrets
import sqlite3
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .canonical_rental import (
    DEFAULT_RENTAL_SERVING_DB,
    canonical_complex_detail,
    canonical_rental_status,
    open_rental_serving_reader,
    recommend_canonical_rentals,
)
from .rental_recommendation import RentalDataUnavailable, RentalInputError
from .rental_recommendation import SEOUL_DISTRICTS
from .http_helpers import discard_rejected_body


STATIC_ROOT = Path(__file__).with_name("static")
MAX_REQUEST_BYTES = 16 * 1024
REQUEST_TIMEOUT_SECONDS = 8
SESSION_TTL_SECONDS = 30 * 60
MAX_CHAT_MESSAGES = 20
MAX_CHAT_TEXT = 2000
MAX_MODEL_REPLY = 1000


class _NoModelRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_args, **_kwargs):
        raise urllib.error.URLError('local model redirects are not allowed')


def _model_request(request, *, timeout):
    # Ignore proxy environment and prohibit redirects away from loopback.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoModelRedirect()).open(request, timeout=timeout)

_CHAT_SYSTEM = """집담 전월세 검색 조건 확인 도우미입니다.
대화에서 사용자가 명시한 조건만 초안에 기록합니다. 숫자는 사용자가 말한 단위가 확실할 때만 원 정수로 바꾸세요.
필수 또는 선호를 추측하지 말고, 전세/월세·예산·지역 중 빠진 값을 확인하는 한국어 질문을 하나 하세요.
부동산 정보를 답하거나 단지를 추천하지 말고, 장소 좌표·DB 내용·시설 존재를 추정하지 마세요.
정확한 JSON 한 개만 출력하세요. 형식: {"reply":"추가 질문 한 문장","draft":{"rental_type":"jeonse 또는 wolse","max_deposit_krw":정수,"max_monthly_rent_krw":정수,"districts":["서울 자치구"],"area_min_sqm":숫자,"area_max_sqm":숫자,"conditions":[{"kind":"station|supermarket|park|hospital|workplace","max_distance_m":숫자,"required":true 또는 false}]}
명시되지 않은 키는 빼세요. 좌표, 임의 장소 ID, 추천 후보는 출력하지 마세요."""


class _RentalHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = False
    daemon_threads = True

    def __init__(self, port: int, *, database: Path, model: str | None, endpoint: str, allow_synthetic: bool = False) -> None:
        self.database = database
        self.model = model
        self.endpoint = endpoint
        self.allow_synthetic = allow_synthetic
        self.csrf_token = secrets.token_urlsafe(32)
        self.sessions: dict[str, dict] = {}
        self.session_lock = threading.Lock()
        super().__init__(("127.0.0.1", port), _RentalRequestHandler)

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.server_port}"


class _RentalRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server: _RentalHTTPServer

    def setup(self) -> None:
        self.request.settimeout(REQUEST_TIMEOUT_SECONDS)
        super().setup()

    def log_message(self, _format: str, *args: object) -> None:
        # Do not write chat text, requested places, or URL values to the console.
        return

    def send_error(self, code: int, message: str | None = None, explain: str | None = None) -> None:
        self._json(code, {"error": "지원하지 않거나 올바르지 않은 HTTP 요청입니다."})

    def _send(self, status: int, body: bytes = b"", *, content_type: str = "application/json; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://tile.openstreetmap.org; "
            "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        )
        self.send_header("Connection", "close")
        self.end_headers()
        if body and self.command != "HEAD":
            try:
                self.wfile.write(body)
            except ConnectionError:
                pass
        self.close_connection = True

    def _json(self, status: int, value: object) -> None:
        body = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")
        self._send(status, body)

    def _route(self) -> str | None:
        try:
            parsed = urllib.parse.urlsplit(self.path)
        except ValueError:
            self._json(400, {"error": "요청 경로가 올바르지 않습니다."})
            return None
        if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
            self._json(400, {"error": "요청 경로가 올바르지 않습니다."})
            return None
        return parsed.path

    def _guard_local(self) -> bool:
        if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
            discard_rejected_body(self, MAX_REQUEST_BYTES)
            self._json(421, {"error": "이 로컬 서버 주소는 허용되지 않습니다."})
            return False
        return True

    def _guard_mutation(self) -> bool:
        if not self._guard_local():
            return False
        origin = self.headers.get("Origin", "")
        token = self.headers.get("X-Jipdam-CSRF", "")
        if origin != self.server.origin or not secrets.compare_digest(
                token.encode("utf-8"), self.server.csrf_token.encode("ascii")):
            discard_rejected_body(self, MAX_REQUEST_BYTES)
            self._json(403, {"error": "로컬 화면에서 다시 요청해 주세요."})
            return False
        return True

    def _body(self) -> dict:
        if self.headers.get_content_type() != "application/json":
            raise RentalInputError("요청 형식은 JSON이어야 합니다.")
        try:
            size = int(self.headers.get("Content-Length", "-1"))
        except ValueError as exc:
            raise RentalInputError("요청 크기를 확인할 수 없습니다.") from exc
        if not 0 <= size <= MAX_REQUEST_BYTES:
            raise RentalInputError("요청 크기가 허용 범위를 벗어났습니다.")
        try:
            body = json.loads(self.rfile.read(size).decode("utf-8"))
        except (ValueError, TimeoutError, OSError) as exc:
            raise RentalInputError("JSON 요청을 읽을 수 없습니다.") from exc
        if not isinstance(body, dict):
            raise RentalInputError("JSON 객체를 보내 주세요.")
        return body

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if not self._guard_local():
            return
        path = self._route()
        if path is None:
            return
        if path == "/":
            try:
                page = (STATIC_ROOT / "rental.html").read_text(encoding="utf-8")
            except OSError:
                self._json(500, {"error": "화면을 불러올 수 없습니다."})
                return
            page = page.replace("__JIPDAM_CSRF_TOKEN__", self.server.csrf_token)
            self._send(200, page.encode("utf-8"), content_type="text/html; charset=utf-8")
            return
        static_types = {"/static/rental.js": "text/javascript; charset=utf-8",
                        "/static/rental.css": "text/css; charset=utf-8"}
        if path in static_types:
            try:
                body = (STATIC_ROOT / path.rsplit("/", 1)[1]).read_bytes()
            except OSError:
                self._json(404, {"error": "정적 파일을 찾을 수 없습니다."})
                return
            self._send(200, body, content_type=static_types[path])
            return
        if path.startswith('/static/vendor/leaflet/'):
            filename = path.removeprefix('/static/vendor/leaflet/')
            allowed = {'leaflet.js': 'text/javascript', 'leaflet.css': 'text/css',
                       'LICENSE': 'text/plain', 'images/marker-icon.png': 'image/png',
                       'images/marker-icon-2x.png': 'image/png', 'images/marker-shadow.png': 'image/png',
                       'images/layers.png': 'image/png', 'images/layers-2x.png': 'image/png'}
            if filename not in allowed:
                self._json(404, {'error': '정적 파일을 찾을 수 없습니다.'})
                return
            try:
                self._send(200, (STATIC_ROOT / 'vendor' / 'leaflet' / filename).read_bytes(), content_type=allowed[filename])
            except OSError:
                self._json(404, {'error': '지도 자산이 없습니다.'})
            return
        if path == "/api/status":
            try:
                connection = open_rental_serving_reader(self.server.database, allow_synthetic=self.server.allow_synthetic)
                try:
                    self._json(200, {**canonical_rental_status(connection), 'model_configured': bool(self.server.model)})
                finally:
                    connection.close()
            except (RentalDataUnavailable, sqlite3.Error):
                self._json(503, {"status": "db_unavailable", "error": "추천 DB를 이용할 수 없습니다. prepare-rentals로 준비해 주세요."})
            return
        if path.startswith("/api/candidates/"):
            parts = path.removeprefix("/api/candidates/").split("/")
            try:
                complex_id = urllib.parse.unquote(parts[0], errors='strict')
                if len(parts) > 2:
                    raise RentalInputError("상세 경로가 올바르지 않습니다.")
                offset = int(parts[1]) if len(parts) == 2 else 0
                connection = open_rental_serving_reader(self.server.database, allow_synthetic=self.server.allow_synthetic)
                try:
                    detail = canonical_complex_detail(connection, complex_id, offset=offset)
                finally:
                    connection.close()
                self._json(404 if detail['status'] == 'not_found' else 200, detail)
            except (RentalDataUnavailable, sqlite3.Error):
                self._json(503, {"status": "db_unavailable", "error": "상세 DB를 이용할 수 없습니다."})
            except (RentalInputError, ValueError) as exc:
                self._json(400, {"status": "input_error", "error": str(exc)})
            return
        self._json(404, {"error": "요청한 경로를 찾을 수 없습니다."})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler contract
        if not self._guard_mutation():
            return
        path = self._route()
        if path is None:
            return
        try:
            body = self._body()
            if path == "/api/chat":
                self._chat(body)
                return
            if path == "/api/recommendations":
                connection = open_rental_serving_reader(self.server.database, allow_synthetic=self.server.allow_synthetic)
                try:
                    result = recommend_canonical_rentals(connection, body.get("request"))
                finally:
                    connection.close()
                self._json(200, result)
                return
            self._json(404, {"error": "요청한 경로를 찾을 수 없습니다."})
        except RentalInputError as exc:
            self._json(400, {"status": "input_error", "error": str(exc)})
        except RentalDataUnavailable as exc:
            self._json(503, {"status": "db_unavailable", "error": str(exc)})
        except sqlite3.Error:
            self._json(503, {"status": "db_unavailable", "error": "추천 DB를 이용할 수 없습니다."})
        except (TimeoutError, OSError):
            self._json(503, {"status": "model_unavailable", "error": "로컬 모델에 연결할 수 없습니다."})
        except Exception:
            self._json(500, {"error": "요청을 처리하지 못했습니다."})

    def _chat(self, body: dict) -> None:
        if body.get('reset') is True:
            with self.server.session_lock:
                session_id = body.get('session_id')
                if isinstance(session_id, str):
                    self.server.sessions.pop(session_id, None)
            self._json(200, {'status': 'reset', 'storage': 'memory_only'})
            return
        message = body.get("message")
        if not isinstance(message, str) or not message.strip() or len(message) > MAX_CHAT_TEXT:
            raise RentalInputError("대화 내용은 1~2000자여야 합니다.")
        try:
            message.encode("utf-8")
        except UnicodeEncodeError:
            raise RentalInputError("대화에 올바르지 않은 문자가 있습니다.") from None
        session_id = body.get("session_id")
        if session_id is not None and (not isinstance(session_id, str) or not 1 <= len(session_id) <= 100):
            raise RentalInputError("대화 세션이 올바르지 않습니다.")
        with self.server.session_lock:
            now = datetime.now(timezone.utc).timestamp()
            self.server.sessions = {
                key: value for key, value in self.server.sessions.items()
                if now - value["updated"] < SESSION_TTL_SECONDS
            }
            if session_id is None:
                if len(self.server.sessions) >= 512:
                    raise RentalInputError('대화 세션이 많습니다. 잠시 후 다시 시작해 주세요.')
                session_id = secrets.token_urlsafe(24)
                session = {"messages": [], "draft": {}, "updated": now}
                self.server.sessions[session_id] = session
            else:
                session = self.server.sessions.get(session_id)
                if not isinstance(session, dict):
                    raise RentalInputError("대화 세션이 만료되었습니다. 새 대화를 시작해 주세요.")
                session["updated"] = now
            if len(session["messages"]) >= MAX_CHAT_MESSAGES:
                raise RentalInputError("대화 횟수가 최대치에 도달했습니다. 조건을 확인해 주세요.")
            if session.get('busy'):
                raise RentalInputError('이전 질문의 답변을 기다려 주세요.')
            session['busy'] = True
            if 'draft' in body:
                session['draft'] = self._safe_draft(body['draft'])
            session["messages"].append({"role": "user", "content": message.strip()})
            messages = list(session["messages"])
            current_draft = dict(session["draft"])
        try:
            reply, draft_patch = self._followup(messages, current_draft)
            mode = "local_llm" if self.server.model else "guided_fallback"
        except (OSError, RentalInputError):
            reply = "대화 내용을 보존했습니다. 전월세 유형과 보증금·월세 상한을 아래 조건에서 직접 확인해 주세요."
            draft_patch = {}
            mode = "guided_fallback"
        with self.server.session_lock:
            current = self.server.sessions.get(session_id)
            result_draft = {**current_draft, **draft_patch}
            if current is not None:
                current['busy'] = False
                current["draft"].update(draft_patch)
                if current["draft"].get("rental_type") == "jeonse":
                    current["draft"]["max_monthly_rent_krw"] = 0
                current["messages"].append({"role": "assistant", "content": reply})
                current["updated"] = datetime.now(timezone.utc).timestamp()
                result_draft = dict(current["draft"])
        self._json(200, {"session_id": session_id, "reply": reply,
                         "draft": result_draft,
                         "draft_patch": draft_patch,
                         "missing_fields": [key for key in ('rental_type','max_deposit_krw','max_monthly_rent_krw')
                                            if key not in result_draft],
                         "message_count": len(messages) + 1, "storage": "memory_only", "mode": mode})

    def _followup(self, messages: list[dict[str, str]], current_draft: dict) -> tuple[str, dict]:
        if not self.server.model:
            return "찾으시는 전월세 유형과 보증금·월세 상한을 알려주세요.", {}
        endpoint = urllib.parse.urlsplit(self.server.endpoint)
        if endpoint.scheme != "http" or endpoint.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise RentalInputError("대화 모델은 로컬 주소만 사용할 수 있습니다.")
        payload = {"model": self.server.model,
                   "messages": [{"role": "system", "content": _CHAT_SYSTEM},
                                {"role": "system", "content": "현재 조건 초안: " + json.dumps(current_draft, ensure_ascii=False)},
                                *messages],
                   "temperature": 0.1, "stream": False}
        request = urllib.request.Request(
            self.server.endpoint, data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            with _model_request(request, timeout=20) as response:
                result = json.loads(response.read(256 * 1024).decode("utf-8"))
            content = result["choices"][0]["message"]["content"]
        except (urllib.error.URLError, TimeoutError, KeyError, IndexError, TypeError,
                UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise OSError("local model unavailable") from exc
        if not isinstance(content, str) or not content.strip():
            raise OSError("local model returned an empty response")
        try:
            parsed = json.loads(content)
            if not isinstance(parsed, dict) or not isinstance(parsed.get("reply"), str):
                raise ValueError("invalid chat response")
            reply = parsed["reply"].strip()
            draft = self._safe_draft(parsed.get("draft", {}))
        except (json.JSONDecodeError, ValueError):
            # Keep the conversation, but do not treat free-form model output as conditions.
            raise OSError("local model response was not valid structured JSON") from None
        if not reply or len(reply) > MAX_MODEL_REPLY or "?" not in reply:
            raise OSError("local model response was not a bounded follow-up question")
        try:
            reply.encode("utf-8")
        except UnicodeEncodeError:
            raise OSError("local model response contains invalid text") from None
        return reply, draft

    @staticmethod
    def _safe_draft(value: object) -> dict:
        if not isinstance(value, dict):
            return {}
        def positive_number(number: object) -> float | None:
            if type(number) not in (int, float):
                return None
            try:
                numeric = float(number)
            except OverflowError:
                return None
            return numeric if math.isfinite(numeric) and numeric > 0 else None

        result = {}
        if isinstance(value.get("rental_type"), str) and value["rental_type"] in {"jeonse", "wolse"}:
            result["rental_type"] = value["rental_type"]
        for key in ("max_deposit_krw", "max_monthly_rent_krw"):
            number = value.get(key)
            if type(number) is int and 0 <= number <= 9_223_372_036_854_775_807:
                result[key] = number
        for key in ("area_min_sqm", "area_max_sqm"):
            if key in value and value[key] is None:
                result[key] = None
                continue
            number = positive_number(value.get(key))
            if number is not None:
                result[key] = number
        districts = value.get("districts")
        if isinstance(districts, list):
            valid = []
            for district in districts:
                if isinstance(district, str) and (district in SEOUL_DISTRICTS or district in SEOUL_DISTRICTS.values()):
                    valid.append(SEOUL_DISTRICTS.get(district, district))
            if valid or not districts:
                result["districts"] = sorted(set(valid))
        conditions = value.get("conditions")
        if isinstance(conditions, list):
            checked = []
            seen = set()
            for condition in conditions:
                distance = positive_number(condition.get("max_distance_m")) if isinstance(condition, dict) else None
                if (isinstance(condition, dict) and isinstance(condition.get("kind"), str) and condition["kind"] in
                        {"station", "supermarket", "park", "hospital", "workplace"} and
                        condition["kind"] not in seen and
                        type(condition.get("required")) is bool and
                        distance is not None):
                    checked.append({"kind": condition["kind"],
                                    "max_distance_m": distance,
                                    "required": condition["required"]})
                    seen.add(condition["kind"])
            if checked or not conditions:
                result["conditions"] = checked
        return result


def create_rental_server(*, port: int = 8766, database: Path = DEFAULT_RENTAL_SERVING_DB,
                         model: str | None = None,
                         endpoint: str | None = None, allow_synthetic: bool = False) -> ThreadingHTTPServer:
    if not 0 <= port <= 65535:
        raise ValueError("port must be between 0 and 65535")
    endpoint = endpoint or os.environ.get('OLLAMA_ENDPOINT', 'http://127.0.0.1:11434/v1/chat/completions')
    parsed = urllib.parse.urlsplit(endpoint)
    if (parsed.scheme != 'http' or parsed.hostname not in {'localhost', '127.0.0.1', '::1'} or
            parsed.username or parsed.password or parsed.fragment):
        raise RentalInputError('대화 모델 엔드포인트는 인증정보 없는 로컬 HTTP 주소여야 합니다.')
    return _RentalHTTPServer(
        port, database=Path(database), model=model or os.environ.get("JIPDAM_RENTAL_MODEL"),
        endpoint=endpoint, allow_synthetic=allow_synthetic,
    )


def serve_rental_mvp(*, port: int = 8766, database: Path = DEFAULT_RENTAL_SERVING_DB,
                     model: str | None = None, endpoint: str | None = None,
                     open_browser: bool = True, allow_synthetic: bool = False) -> None:
    server = create_rental_server(port=port, database=database, model=model, endpoint=endpoint, allow_synthetic=allow_synthetic)
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"집담 전월세 MVP: {url}")
    print("로컬 서버에서만 실행합니다. 대화 내용은 메모리에만 유지됩니다. 종료: Ctrl+C")
    if open_browser:
        try:
            webbrowser.open(url, new=2, autoraise=False)
        except Exception:
            pass
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        print("\n전월세 MVP 서버를 종료합니다.")
    finally:
        server.server_close()

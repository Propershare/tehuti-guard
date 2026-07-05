# flake8: noqa: E501
"""Minimal HTTP: POST /decision, POST /explain, GET /health, …"""

from __future__ import annotations

import json
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from tehuti_guard import POLICY_VERSION, __version__
from tehuti_guard.covenant_adapter import compile_request
from tehuti_guard.memory_sink import (
    log_compile_decision_row,
    log_guard_decision_row,
    log_guard_explanation_row,
)
from tehuti_guard.models import DecisionRequest
from tehuti_guard.rules import (
    compute_explanation_id,
    evaluate_compiler_with_rules,
    evaluate_with_rules,
    explain_envelope,
    policy_rules_document,
)
from tehuti_guard.sentinel import default_sentinel_base, fetch_unified_view


def _read_json(handler: BaseHTTPRequestHandler) -> dict[str, Any] | None:
    n = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(n) if n else b""
    if not raw:
        return {}
    try:
        out = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return None
    return out if isinstance(out, dict) else None


def _json(handler: BaseHTTPRequestHandler, code: int, body: dict[str, Any]) -> None:
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)


class GuardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/health":
            _json(
                self,
                200,
                {"ok": True, "service": "tehuti-guard-api", "version": __version__},
            )
            return
        if path == "/policy-version":
            _json(self, 200, {"policy_version": POLICY_VERSION})
            return
        if path == "/rules":
            _json(self, 200, policy_rules_document())
            return
        _json(self, 404, {"error": "not_found"})

    def do_POST(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path not in ("/decision", "/explain", "/compile-decision"):
            _json(self, 404, {"error": "not_found"})
            return
        data = _read_json(self)
        if data is None:
            _json(self, 400, {"error": "invalid_json"})
            return
        cid = (data.get("correlation_id") or "").strip() or None
        if not cid:
            hdr = self.headers.get("X-Correlation-ID") or self.headers.get("x-correlation-id")
            if hdr:
                cid = hdr.strip()
        if not cid:
            cid = str(uuid.uuid4())
        data["correlation_id"] = cid
        try:
            req = DecisionRequest.from_dict(data)
        except (TypeError, KeyError, ValueError):
            _json(self, 400, {"error": "invalid_envelope"})
            return

        view = fetch_unified_view(req.machine_id)
        if path == "/compile-decision":
            try:
                compiler_result = compile_request(req)
            except Exception as e:
                _json(
                    self,
                    500,
                    {
                        "error": "compile_failed",
                        "message": str(e),
                        "correlation_id": cid,
                        "policy_version": POLICY_VERSION,
                    },
                )
                return
            result, matched_rules = evaluate_compiler_with_rules(
                req,
                view,
                compiler_result,
            )
            explanation_id = compute_explanation_id(req, matched_rules)
            out = {
                **result.to_dict(),
                "matched_rules": matched_rules,
                "explanation_id": explanation_id,
                "policy_version": POLICY_VERSION,
                "sentinel_url": default_sentinel_base(),
                "correlation_id": cid,
                "compiler_result": compiler_result,
            }
            if os.environ.get("TEHUTI_GUARD_INCLUDE_SENTINEL_VIEW", "").lower() in (
                "1",
                "true",
                "yes",
            ):
                out["sentinel_view"] = view
            log_compile_decision_row(data, out)
            _json(self, 200, out)
            return

        if path == "/explain":
            out: dict[str, Any] = {
                **explain_envelope(req, view),
                "policy_version": POLICY_VERSION,
                "correlation_id": cid,
            }
            if os.environ.get("TEHUTI_GUARD_INCLUDE_SENTINEL_VIEW", "").lower() in (
                "1",
                "true",
                "yes",
            ):
                out["sentinel_view"] = view
            log_guard_explanation_row(data, out)
            _json(self, 200, out)
            return

        result, matched_rules = evaluate_with_rules(req, view)
        explanation_id = compute_explanation_id(req, matched_rules)
        out = {
            **result.to_dict(),
            "matched_rules": matched_rules,
            "explanation_id": explanation_id,
            "policy_version": POLICY_VERSION,
            "sentinel_url": default_sentinel_base(),
            "correlation_id": cid,
        }
        if os.environ.get("TEHUTI_GUARD_INCLUDE_SENTINEL_VIEW", "").lower() in ("1", "true", "yes"):
            out["sentinel_view"] = view
        log_guard_decision_row(data, out)
        _json(self, 200, out)

    def log_message(self, fmt: str, *args: object) -> None:
        return


def default_port() -> int:
    raw = os.environ.get("TEHUTI_GUARD_PORT", "").strip()
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return 8013


def run_server(host: str, port: int) -> None:
    import sys

    print(
        f"tehuti-guard-api http://{host}:{port}  "
        f"POST /decision /explain /compile-decision  "
        f"GET /health /policy-version /rules",
        file=sys.stderr,
    )
    server = ThreadingHTTPServer((host, port), GuardHandler)
    server.serve_forever()

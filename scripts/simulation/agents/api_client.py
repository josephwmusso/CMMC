"""HTTP wrapper with session auth, retries, and request/response logging."""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import requests


class ApiClient:
    def __init__(self, base_url: str, run_dir: Path, verbose: bool = False):
        self.base_url = base_url.rstrip("/")
        self.run_dir = run_dir
        self.verbose = verbose
        self.session = requests.Session()
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.org_id: Optional[str] = None
        self.user_id: Optional[str] = None
        self._log: list[dict] = []

    def login(self, email: str, password: str) -> dict:
        resp = self.session.post(
            f"{self.base_url}/api/auth/login",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        if data.get("user"):
            self.user_id = data["user"].get("id")
            self.org_id = data["user"].get("org_id")
        return data

    def set_tokens(self, access: str, refresh: str, org_id: str = None, user_id: str = None):
        self.access_token = access
        self.refresh_token = refresh
        if org_id:
            self.org_id = org_id
        if user_id:
            self.user_id = user_id

    def clear_auth(self):
        self.access_token = None
        self.refresh_token = None
        self.org_id = None
        self.user_id = None

    def refresh(self) -> bool:
        if not self.refresh_token:
            return False
        try:
            resp = self.session.post(
                f"{self.base_url}/api/auth/refresh",
                json={"refresh_token": self.refresh_token},
            )
            if resp.ok:
                self.access_token = resp.json().get("access_token")
                return True
        except Exception:
            pass
        return False

    def get(self, path: str, **kwargs) -> requests.Response:
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        return self._request("POST", path, **kwargs)

    def patch(self, path: str, **kwargs) -> requests.Response:
        return self._request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        return self._request("DELETE", path, **kwargs)

    def post_multipart(self, path: str, files: dict, data: dict = None) -> requests.Response:
        return self._request("POST", path, files=files, data=data)

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        if "json" in kwargs and "Content-Type" not in headers and "files" not in kwargs:
            headers.setdefault("Content-Type", "application/json")

        t0 = time.monotonic()
        attempt = 0
        max_retries = 3
        resp = None

        while attempt < max_retries:
            try:
                resp = self.session.request(method, url, headers=headers, timeout=300, **kwargs)
            except requests.exceptions.RequestException as e:
                attempt += 1
                if attempt >= max_retries:
                    raise
                time.sleep(min(2 ** attempt, 8))
                continue

            if resp.status_code == 401 and attempt == 0 and self.refresh():
                headers["Authorization"] = f"Bearer {self.access_token}"
                attempt += 1
                continue
            if resp.status_code >= 500 and attempt < max_retries - 1:
                attempt += 1
                time.sleep(min(2 ** attempt, 8))
                continue
            break

        duration = int((time.monotonic() - t0) * 1000)

        # Log entry
        req_body = kwargs.get("json") or kwargs.get("data")
        if isinstance(req_body, dict):
            req_body = {k: ("***" if k in ("password", "access_token", "refresh_token") else v)
                        for k, v in req_body.items()}
        resp_body = None
        try:
            resp_body = resp.json() if resp else None
        except Exception:
            resp_body = resp.text[:2048] if resp else None
        if isinstance(resp_body, dict):
            for redact_key in ("access_token", "refresh_token"):
                if redact_key in resp_body:
                    resp_body[redact_key] = "***"

        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "path": path,
            "status": resp.status_code if resp else 0,
            "duration_ms": duration,
        }
        if self.verbose:
            entry["request_body"] = req_body
            entry["response_body"] = str(resp_body)[:2048] if resp_body else None

        self._log.append(entry)
        if self.verbose:
            print(f"  {method} {path} → {resp.status_code if resp else '???'} ({duration}ms)")

        return resp

    def flush_log(self):
        path = self.run_dir / "journey.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self._log, f, indent=2, default=str)

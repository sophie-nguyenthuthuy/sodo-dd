from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential


@dataclass(slots=True)
class AdapterResponse:
    name: str
    url: str | None
    status: str  # ok | no_data | error
    queried_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    @property
    def response_hash(self) -> str:
        canonical = json.dumps(self.payload, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class BaseAdapter(ABC):
    name: str = "base"
    base_url: str | None = None
    timeout: float = 20.0

    def __init__(self, *, mode: str = "mock", api_key: str | None = None):
        self.mode = mode
        self.api_key = api_key

    # ─── public
    def query(self, **kwargs: Any) -> AdapterResponse:
        if self.mode == "mock":
            return self._mock(**kwargs)
        return self._live(**kwargs)

    # ─── overrides
    @abstractmethod
    def _live(self, **kwargs: Any) -> AdapterResponse: ...

    @abstractmethod
    def _mock(self, **kwargs: Any) -> AdapterResponse: ...

    # ─── helpers
    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
        wait=wait_exponential(min=0.5, max=4),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _http_get(self, url: str, *, params: dict[str, Any] | None = None) -> httpx.Response:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        with httpx.Client(timeout=self.timeout, headers=headers) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            return resp

    def _ok(self, payload: dict, url: str | None = None) -> AdapterResponse:
        return AdapterResponse(self.name, url, "ok", datetime.now(UTC), payload)

    def _no_data(self, url: str | None = None) -> AdapterResponse:
        return AdapterResponse(self.name, url, "no_data", datetime.now(UTC), {})

    def _error(self, msg: str, url: str | None = None) -> AdapterResponse:
        return AdapterResponse(self.name, url, "error", datetime.now(UTC), {}, error=msg)

from __future__ import annotations

import asyncio
import json as jsonlib
from typing import Any, Dict, Optional
from urllib.parse import urlencode, urljoin, urlparse


class Response:
    def __init__(self, status_code: int, body: bytes, headers: Dict[bytes, bytes]) -> None:
        self.status_code = status_code
        self._body = body
        self._headers = headers

    def json(self) -> Any:
        return jsonlib.loads(self._body.decode()) if self._body else None

    @property
    def text(self) -> str:
        return self._body.decode()


class AsyncClient:
    def __init__(self, app, base_url: str = "http://testserver") -> None:
        self.app = app
        self.base_url = base_url.rstrip("/") + "/"

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def request(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        json: Any = None,
        data: Any = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Response:
        path_url = url.lstrip("/")
        if params:
            path_url = f"{path_url}?{urlencode(params, doseq=True)}"
        request_url = urljoin(self.base_url, path_url)
        parsed = urlparse(request_url)
        path = parsed.path or "/"
        query_string = parsed.query.encode()

        send_channel: asyncio.Queue = asyncio.Queue()
        receive_channel: asyncio.Queue = asyncio.Queue()

        if json is not None:
            body = jsonlib.dumps(json).encode()
            content_type = "application/json"
        elif data is not None:
            if isinstance(data, dict):
                body = urlencode(data).encode()
            elif isinstance(data, str):
                body = data.encode()
            else:
                body = data
            content_type = "application/x-www-form-urlencoded"
        else:
            body = b""
            content_type = "application/octet-stream"

        await receive_channel.put({"type": "http.request", "body": body, "more_body": False})

        headers = headers or {}
        default_headers = {"host": parsed.netloc or "testserver", "content-type": content_type}
        raw_headers = [(key.lower().encode(), str(value).encode()) for key, value in {**default_headers, **headers}.items()]

        scope = {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.3"},
            "method": method.upper(),
            "scheme": parsed.scheme,
            "path": path,
            "raw_path": path.encode(),
            "query_string": query_string,
            "headers": raw_headers,
            "client": (parsed.hostname or "testserver", 80),
            "server": (parsed.hostname or "testserver", parsed.port or 80),
        }

        async def receive():
            return await receive_channel.get()

        async def send(message):
            await send_channel.put(message)

        await self.app(scope, receive, send)

        status_code = 500
        body = b""
        response_headers: Dict[bytes, bytes] = {}
        while not send_channel.empty():
            message = await send_channel.get()
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers = dict(message.get("headers", []))
            elif message["type"] == "http.response.body":
                body += message.get("body", b"")
        return Response(status_code=status_code, body=body, headers=response_headers)

    async def get(self, url: str, **kwargs: Any) -> Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> Response:
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> Response:
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> Response:
        return await self.request("DELETE", url, **kwargs)

import asyncio
import json
import logging

from app.core.logging import JSONFormatter
from app.main import app


def test_json_formatter_includes_core_fields_and_extra_metadata():
    formatter = JSONFormatter()
    record = logging.makeLogRecord(
        {
            "name": "agentic_vision",
            "levelno": logging.INFO,
            "levelname": "INFO",
            "msg": "request completed",
            "module": "main",
            "created": 1_700_000_000.0,
            "request_method": "POST",
            "status_code": 200,
        }
    )

    payload = json.loads(formatter.format(record))

    assert payload["level"] == "INFO"
    assert payload["message"] == "request completed"
    assert payload["module"] == "main"
    assert payload["extra"]["request_method"] == "POST"
    assert payload["extra"]["status_code"] == 200


def test_request_middleware_adds_process_time_header():
    async def invoke_app() -> tuple[dict, list[dict]]:
        messages: list[dict] = []

        async def receive() -> dict:
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message: dict) -> None:
            messages.append(message)

        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "path": "/health",
            "raw_path": b"/health",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
            "scheme": "http",
            "root_path": "",
            "extensions": {},
        }
        await app(scope, receive, send)
        return scope, messages

    _, messages = asyncio.run(invoke_app())
    start_message = next(message for message in messages if message["type"] == "http.response.start")
    headers = {
        key.decode("latin1"): value.decode("latin1")
        for key, value in start_message["headers"]
    }

    assert start_message["status"] == 200
    assert "x-process-time-ms" in headers

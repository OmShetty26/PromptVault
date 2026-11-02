import asyncio
import json

from fastapi import Request

from main import unhandled_exception_handler


def test_unhandled_exception_returns_generic_500():
    request = Request({
        "type": "http",
        "method": "GET",
        "path": "/test",
        "headers": [],
        "query_string": b"",
        "server": ("testserver", 80),
        "client": ("testclient", 50000),
        "scheme": "http",
    })

    try:
        raise RuntimeError("Sensitive internal error")
    except RuntimeError as exc:
        response = asyncio.run(
            unhandled_exception_handler(request, exc)
        )

    assert response.status_code == 500
    assert json.loads(response.body) == {
        "detail": "Internal server error"
    }
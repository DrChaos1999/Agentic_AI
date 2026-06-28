from __future__ import annotations

from fastapi import Request

from app.services.runtime import RuntimeServices


def get_runtime(request: Request) -> RuntimeServices:
    return request.app.state.runtime

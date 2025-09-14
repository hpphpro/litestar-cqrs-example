from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import (
    Any,
)
from urllib.parse import urlencode

from litestar import Request
from litestar.datastructures import State
from litestar.enums import ScopeType

from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import Context


@dataclass(slots=True, frozen=True)
class HttpContext(Context):
    request_id: str
    request_method: str
    request_path: str
    request_path_params: Mapping[str, Any]
    request_query_params: Mapping[str, Any]
    request_json_params: Mapping[str, Any]
    request_url: str


async def context_from_request(request: Request[Any, Any, State]) -> HttpContext:
    if request.scope["type"] != ScopeType.HTTP:
        raise exc.ServiceNotImplemented("ASGI connection is not an HTTP connection")

    return HttpContext(
        request_id=request.headers.get("x-request-id", request.state["request_id"]),
        user=request.scope.get("user"),
        request_method=request.scope["method"],
        request_path=request.scope["path"],
        request_path_params=request.path_params,
        request_query_params=dict(request.query_params),
        request_json_params=(await request.json()) or {},
        request_url=str(request.url),
    )


def _sort_by_key(value: tuple[str, Any]) -> str:
    return value[0]


def cache_request_key_builder(ctx: Context) -> str:
    return (
        f"{ctx.request_method or ''}{ctx.request_path or ''}"
        f"{urlencode(sorted(ctx.request_query_params.items(), key=_sort_by_key), doseq=True)}"
        f"{ctx.user.id if ctx.user else ''}"
    )

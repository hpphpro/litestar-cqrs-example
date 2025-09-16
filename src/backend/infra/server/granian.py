import socket
from typing import Any

from granian.constants import Interfaces
from granian.server import Server as Granian

from config.core import BackendConfig


def run_granian(
    target: str,
    config: BackendConfig,
    **kw: Any,
) -> None:
    workers = max(1, config.server.workers_count())
    backpressure = max(100, config.compute_concurrency_limit(workers)) if workers > 1 else None
    options = {
        "address": config.server.host,
        "port": config.server.port,
        "workers": workers,
        "log_access": config.server.log,
        "interface": Interfaces.ASGI,
        "log_access_format": (
            '[%(time)s] %(addr)s - "%(method)s %(path)s %(query_string)s '
            '%(protocol)s" %(status)d %(dt_ms).3f'
        ),
        "backpressure": backpressure,
        "backlog": max(2048, socket.SOMAXCONN),
    }

    server = Granian(
        target,
        **{**options, **kw},
    )

    server.serve()  # type: ignore[attr-defined]

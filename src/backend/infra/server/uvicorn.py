import socket
from typing import Any

import uvicorn

from config.core import BackendConfig


def run_uvicorn(app: Any, config: BackendConfig, **kw: Any) -> None:
    workers = max(1, config.server.workers_count())
    limit_concurrency = max(100, config.compute_concurrency_limit(workers)) if workers > 1 else None
    options = {
        "workers": workers,
        "host": config.server.host,
        "port": config.server.port,
        "access_log": config.server.log,
        "limit_concurrency": limit_concurrency,
        "backlog": max(2048, socket.SOMAXCONN),
    }
    uvicorn.run(
        app,
        **{**options, **kw},
    )

from typing import Any

import uvicorn

from config.core import BackendConfig


def run_uvicorn(app: Any, config: BackendConfig, **kw: Any) -> None:
    uvicorn.run(
        app,
        workers=config.server.workers_count(),
        host=config.server.host,
        port=config.server.port,
        access_log=config.server.log,
        limit_concurrency=config.compute_concurrency_limit(),
        **kw,
    )

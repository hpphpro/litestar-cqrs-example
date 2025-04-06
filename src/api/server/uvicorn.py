from typing import Any

import uvicorn

from src.config.core import ServerConfig

from ._util import workers_count


def run_uvicorn(app: Any, config: ServerConfig, **kw: Any) -> None:
    uv_config = uvicorn.Config(
        app,
        host=config.host,
        port=config.port,
        workers=config.workers if config.workers != "auto" else workers_count(),
        timeout_keep_alive=config.timeout,
        access_log=config.log,
        **kw,
    )
    server = uvicorn.Server(uv_config)

    server.run()

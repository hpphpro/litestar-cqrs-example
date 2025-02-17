from typing import Any

from granian import Granian
from granian.constants import Interfaces

from src.core.config import ServerConfig

from ._util import workers_count


def run_granian(
    target: Any,
    config: ServerConfig,
    **kw: Any,
) -> None:
    server = Granian(
        target,
        address=config.host,
        port=config.port,
        workers=config.workers if config.workers != "auto" else workers_count(),
        threads=config.threads,
        log_access=config.log,
        interface=Interfaces.ASGI,
        **kw,
    )

    server.serve()

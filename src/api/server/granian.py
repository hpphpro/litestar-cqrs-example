from typing import Any

from granian.constants import Interfaces
from granian.server import Server as Granian

from src.config.core import ServerConfig

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
        runtime_threads=config.threads,
        log_access=config.log,
        interface=Interfaces.ASGI,
        **kw,
    )

    server.serve()  # type: ignore[attr-defined]

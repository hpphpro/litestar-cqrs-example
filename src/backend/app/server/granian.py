from typing import Any

from granian.constants import Interfaces
from granian.server import Server as Granian

from config.core import BackendConfig


def run_granian(
    target: str,
    config: BackendConfig,
    **kw: Any,
) -> None:
    server = Granian(
        target,
        address=config.server.host,
        port=config.server.port,
        workers=config.server.workers_count(),
        log_access=config.server.log,
        interface=Interfaces.ASGI,
        log_access_format=(
            '[%(time)s] %(addr)s - "%(method)s %(path)s %(query_string)s '
            '%(protocol)s" %(status)d %(dt_ms).3f'
        ),
        backpressure=config.compute_concurrency_limit(),
        **kw,
    )

    server.serve()  # type: ignore[attr-defined]

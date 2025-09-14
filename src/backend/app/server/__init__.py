from typing import Any, assert_never

from config.core import BackendConfig

from .granian import run_granian
from .gunicorn import run_gunicorn
from .uvicorn import run_uvicorn


def serve(app: Any, config: BackendConfig, suffix: str = "app", **kw: Any) -> None:
    target = f"backend.__main__:{suffix}"
    match config.server.type:
        case "granian":
            run_granian(target, config, **kw)
        case "gunicorn":
            run_gunicorn(app, config, **kw)
        case "uvicorn":
            run_uvicorn(target, config, **kw)
        case _:
            assert_never(config.server.type)

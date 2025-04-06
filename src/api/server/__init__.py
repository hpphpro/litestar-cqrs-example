from typing import Any

from src.config.core import ServerConfig

from .granian import run_granian
from .gunicorn import run_gunicorn
from .uvicorn import run_uvicorn


def serve(app: Any, config: ServerConfig, suffix: str = "app", **kw: Any) -> None:
    match config.type:
        case "granian":
            run_granian(f"src.__main__:{suffix}", config, **kw)
        case "gunicorn":
            run_gunicorn(app, config, **kw)
        case "uvicorn":
            run_uvicorn(app, config, **kw)

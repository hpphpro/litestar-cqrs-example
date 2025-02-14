from typing import Any

from src.core.config import ServerConfig
from src.core.server.granian import run_granian
from src.core.server.gunicorn import run_gunicorn
from src.core.server.uvicorn import run_uvicorn


def serve(app: Any, config: ServerConfig, suffix: str = "app", **kw: Any) -> None:
    match config.type:
        case "granian":
            run_granian(f"src.__main__:{suffix}", config, **kw)
        case "gunicorn":
            run_gunicorn(app, config, **kw)
        case "uvicorn":
            run_uvicorn(app, config, **kw)

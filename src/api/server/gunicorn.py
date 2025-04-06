# mypy: ignore-errors

from typing import Any

from gunicorn.app.base import Application

from src.config.core import ServerConfig

from ._util import workers_count


class GunicornApplication(Application):
    def __init__(self, app: Any, options: dict[str, Any] | None = None, **kw: Any) -> None:
        self._options = options or {}
        self._app = app
        super().__init__(**kw)

    def load_config(self) -> None:
        for key, value in self._options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key.lower(), value)

    def load(self) -> Any:
        return self._app


def run_gunicorn(app: Any, config: ServerConfig, **kw: Any) -> None:
    options = {
        "bind": f"{config.host}:{config.port}",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "preload_app": True,
        "timeout": config.timeout,
        "workers": config.workers if config.workers != "auto" else workers_count(),
        "accesslog": "-" if config.log else None,
        "threads": config.threads,
    }
    gunicorn_app = GunicornApplication(app, options | kw)

    gunicorn_app.run()

# mypy: ignore-errors

from typing import Any

from gunicorn.app.base import Application
from gunicorn.glogging import CONFIG_DEFAULTS

from config.core import BackendConfig


class GunicornApp(Application):
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


def run_gunicorn(app: Any, config: BackendConfig, **kw: Any) -> None:
    options = {
        "bind": f"{config.server.host}:{config.server.port}",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "preload_app": False,
        "workers": config.server.workers_count(),
        "accesslog": "-" if config.server.log else None,
        "errorlog": "-" if config.server.log else None,
        "capture_output": True,
        "logconfig_dict": CONFIG_DEFAULTS,
        "reuse_port": True,
    }
    gunicorn_app = GunicornApp(app, options | kw)

    gunicorn_app.run()

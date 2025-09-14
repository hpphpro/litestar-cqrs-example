from contextlib import suppress
from typing import Final

from litestar import Litestar

from backend.app.server import serve
from backend.http import init_app
from backend.http.v1 import init_v1_router
from config.core import BackendConfig, load_config


config: Final[BackendConfig] = load_config()
app: Final[Litestar] = init_app(config, init_v1_router())


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        serve(app, config=config)

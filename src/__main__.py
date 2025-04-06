from contextlib import suppress

from src.api import init_app
from src.api.server import serve
from src.api.v1 import init_v1_router
from src.config.core import load_config


config = load_config()
app = init_app(config, init_v1_router(config=config))


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        serve(app, config=config.server)

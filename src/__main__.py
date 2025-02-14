from contextlib import suppress

from src.api import init_app
from src.api.v1 import init_v1_router
from src.core.config import load_config
from src.core.server import serve


config = load_config()
app = init_app(config, init_v1_router(config=config))


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        serve(app, config=config.server)

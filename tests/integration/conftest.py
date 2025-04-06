import os
from collections.abc import AsyncIterator, Iterator

import alembic.command
import pytest
from alembic.config import Config as AlembicConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from src.api import init_app
from src.api.v1 import init_v1_router
from src.config.core import Config as AppConfig
from src.config.core import DbConfig, RedisConfig, absolute_path, load_config
from src.database.alchemy.core import ConnectionFactory


pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def db_config() -> Iterator[DbConfig]:
    pg = PostgresContainer()

    if os.name == "nt":
        pg.get_container_host_ip = lambda: "127.0.0.1"

    with pg:
        yield DbConfig(
            driver="postgresql+asyncpg",
            name=pg.dbname,
            host=pg.get_container_host_ip(),
            port=pg.get_exposed_port(pg.port),
            user=pg.username,
            password=pg.password,
        )


@pytest.fixture(scope="session")
def redis_config() -> Iterator[RedisConfig]:
    redis = RedisContainer()

    if os.name == "nt":
        redis.get_container_host_ip = lambda: "127.0.0.1"

    with redis:
        yield RedisConfig(
            host=redis.get_container_host_ip(), port=redis.get_exposed_port(redis.port)
        )


@pytest.fixture(scope="session")
def alembic_config(db_config: DbConfig) -> AlembicConfig:
    cfg = AlembicConfig(absolute_path("alembic.ini"))

    cfg.set_main_option("sqlalchemy.url", db_config.url())

    return cfg


@pytest.fixture(scope="session")
def app_config(redis_config: RedisConfig, db_config: DbConfig) -> AppConfig:
    config = load_config(redis=redis_config, db=db_config)

    return config


@pytest.fixture()
def connection(alembic_config: AlembicConfig, db_config: DbConfig) -> Iterator[ConnectionFactory]:
    connection = ConnectionFactory.from_url(db_config.url())

    alembic.command.upgrade(alembic_config, "head")

    yield connection

    alembic.command.downgrade(alembic_config, "base")

    connection.engine.sync_engine.dispose()


@pytest.fixture(scope="function")
async def app(app_config: AppConfig) -> Litestar:
    app = init_app(app_config, init_v1_router(config=app_config))

    return app


@pytest.fixture(scope="function")
async def client(
    app: Litestar, connection: ConnectionFactory
) -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app) as client:
        yield client

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from typing import Final, Literal
from urllib.parse import urljoin

import alembic.command
import pytest
from alembic.config import Config as AlembicConfig
from litestar import Litestar
from litestar.testing import AsyncTestClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from backend.app.contracts.cache import StrCache
from backend.app.contracts.manager import TransactionManager
from backend.http import init_app
from backend.http.v1 import init_v1_router
from backend.infra.database.alchemy.connection import ConnectionFactory
from backend.infra.database.manager import ManagerFactory
from config.core import BackendConfig, DbConfig, RedisConfig, SecurityConfig, absolute_path, load_config
from backend.infra.cache.redis import RedisCache
from uuid_utils import uuid4

TEST_URL: Final[str] = 'http://testserver.local'
pytestmark = pytest.mark.anyio


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def db_config() -> Iterator[DbConfig]:
    pg = PostgresContainer(image="cleisonfmelo/postgres-pg-cron:latest")
    pg = pg.with_command(f"postgres -c shared_preload_libraries=pg_cron -c cron.database_name={pg.dbname}")

    if os.name == "nt":
        pg.get_container_host_ip = lambda: "127.0.0.1"

    with pg:
        host = pg.get_container_host_ip()
        yield DbConfig(
            driver="postgresql+asyncpg",
            name=pg.dbname,
            host=host,
            port=pg.get_exposed_port(pg.port),
            user=pg.username,
            password=pg.password,
            replica_host=host,
        )


@pytest.fixture(scope="session")
def redis_config() -> Iterator[RedisConfig]:
    redis = RedisContainer()

    if os.name == "nt":
        redis.get_container_host_ip = lambda: "127.0.0.1"

    with redis:
        yield RedisConfig(
            host=redis.get_container_host_ip(),
            port=redis.get_exposed_port(redis.port),
        )


@pytest.fixture(scope="session")
def alembic_config(db_config: DbConfig) -> AlembicConfig:
    cfg = AlembicConfig(absolute_path("alembic.ini"))

    cfg.set_main_option("sqlalchemy.url", db_config.url())

    return cfg


@pytest.fixture(scope="session")
def app_config(redis_config: RedisConfig, db_config: DbConfig) -> BackendConfig:
    secret = uuid4().hex
    config = load_config(
        redis=redis_config,
        db=db_config,
        security=SecurityConfig(
            algorithm="HS256",
            secret_key=secret,
            public_key=secret,
            access_token_expire_seconds=3600,
            refresh_token_expire_seconds=86400
        )
    )

    return config


@pytest.fixture(scope="function")
async def cache(redis_config: RedisConfig) -> AsyncIterator[StrCache]:
    cache = RedisCache.from_url(redis_config.url)
    yield cache
    await cache.close()


@pytest.fixture(scope="function")
def connection(alembic_config: AlembicConfig, db_config: DbConfig) -> Iterator[ConnectionFactory]:
    connection = ConnectionFactory.from_url(db_config.url())

    alembic.command.upgrade(alembic_config, "head")

    yield connection

    alembic.command.downgrade(alembic_config, "base")

    connection.engine.sync_engine.dispose()


@pytest.fixture(scope="function")
async def manager(connection: ConnectionFactory) -> AsyncIterator[TransactionManager]:
    async with ManagerFactory(connection).make_manager_context() as ctx:
        yield ctx


@pytest.fixture(scope="function")
async def app(app_config: BackendConfig, connection: ConnectionFactory) -> Litestar:
    app = init_app(app_config, init_v1_router())

    return app


@pytest.fixture(scope="function")
async def client(
    app: Litestar,
    app_config: BackendConfig,
    cache: StrCache,
    anyio_backend: Literal["asyncio", "trio"],
) -> AsyncIterator[AsyncTestClient[Litestar]]:
    async with AsyncTestClient(app, base_url=urljoin(TEST_URL, app_config.api.root_path), backend=anyio_backend) as client:
        yield client
        await cache.clear()

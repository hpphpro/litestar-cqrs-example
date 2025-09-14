from __future__ import annotations

import math
import multiprocessing as mp
import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Literal
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict


if TYPE_CHECKING:
    import _typeshed

type ServerType = Literal["granian", "uvicorn", "gunicorn"]


def root_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def absolute_path(
    *paths: _typeshed.StrPath | Path,
    base_path: _typeshed.StrPath | Path | None = None,
) -> str:
    if base_path is None:
        base_path = root_dir()

    return os.path.join(base_path, *paths)  # noqa: PTH118


class DbConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=absolute_path(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="DB_",
        extra="ignore",
    )
    driver: str = ""
    name: str = ""
    host: str | None = None
    port: int | None = None
    user: str | None = None
    password: str | None = None
    replica_host: str | None = None
    replica_user: str = "replicator"
    replica_password: str | None = None
    connection_timeout: int = 10
    min_connections: int = 10
    ping_connection: bool = True
    max_connections: int = 100
    replica_max_connections: int = 100

    def url(self, *, use_replica: bool = False) -> str:
        if self.driver.startswith("sqlite"):
            return f"{self.driver}:///{self.name}"

        host = self.replica_host if use_replica and self.replica_host else self.host
        return (
            f"{self.driver}://{self.user}:{quote(self.password or '')}@"
            f"{host}:{self.port}/{self.name}"
        )


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=absolute_path(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="SERVER_",
        extra="ignore",
    )
    host: str = "127.0.0.1"
    port: int = 9393
    type: ServerType = "granian"
    workers: int | Literal["auto"] = "auto"
    log: bool = True
    strategy: Strategy = "throughput"

    def workers_count(self) -> int:
        if self.workers == "auto":
            return mp.cpu_count() - 1

        return self.workers


class ApiConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=absolute_path(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="APP_",
        extra="ignore",
    )
    root_path: str = "/api"
    title: str = "Example"
    debug: bool = True
    debug_detailed: bool = False
    version: str = "0.0.1"
    metrics: bool = True
    swagger: bool = True


class RedisConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=absolute_path(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 6379
    password: str | None = None
    username: str | None = None
    db: int = 0

    @property
    def url(self) -> str:
        if self.password and self.username:
            return (
                f"redis://{self.username}:{quote(self.password)}@{self.host}:{self.port}/{self.db}"
            )
        elif self.password:
            return f"redis://:{quote(self.password)}@{self.host}:{self.port}/{self.db}"

        return f"redis://{self.host}:{self.port}/{self.db}"


class SecurityConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=absolute_path(".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="SECURITY_",
        extra="ignore",
    )
    algorithm: str = ""
    secret_key: str = ""
    public_key: str = ""
    access_token_expire_seconds: int = 0
    refresh_token_expire_seconds: int = 0


type Strategy = Literal["stable", "throughput"]


@dataclass(slots=True, frozen=True)
class PoolPerWorkerData:
    pool_size: int
    overflow: int


class BackendConfig(BaseSettings):
    api: ApiConfig
    db: DbConfig
    server: ServerConfig
    redis: RedisConfig
    security: SecurityConfig

    def compute_min_max_connections_per_worker(
        self,
        *,
        total_min: int | None = None,
        total_max: int | None = None,
        workers: int | None = None,
        strategy: Strategy | None = None,
        overflow_target_per_worker: int = 1,
    ) -> PoolPerWorkerData:
        total_min = total_min or self.db.min_connections
        total_max = total_max or self.db.max_connections
        strategy = strategy or self.server.strategy
        workers = workers or self.server.workers_count()

        workers = max(workers, 1)
        if total_max < total_min:
            raise ValueError("max_connections must be >= min_connections")

        per_worker_max = max(1, math.ceil(total_max / workers))
        if strategy == "stable":
            pool_size = max(1, total_min // workers)
            overflow = max(0, per_worker_max - pool_size)
        else:
            pool_size = max(1, per_worker_max - max(0, overflow_target_per_worker))

            pool_size = max(pool_size, math.ceil(total_min / workers))

            pool_size = min(pool_size, per_worker_max)

            overflow = max(0, per_worker_max - pool_size)

        return PoolPerWorkerData(pool_size, overflow)

    def compute_concurrency_limit(
        self,
        workers: int | None = None,
    ) -> int:
        workers = workers or self.server.workers_count()
        return max(1, math.ceil(self.db.max_connections / workers)) + max(
            1, math.ceil(self.db.replica_max_connections / workers)
        )


def load_config(
    db: DbConfig | None = None,
    api: ApiConfig | None = None,
    server: ServerConfig | None = None,
    redis: RedisConfig | None = None,
    security: SecurityConfig | None = None,
) -> BackendConfig:
    return BackendConfig(
        db=db or DbConfig(),
        api=api or ApiConfig(),
        server=server or ServerConfig(),
        redis=redis or RedisConfig(),
        security=security or SecurityConfig(),
    )

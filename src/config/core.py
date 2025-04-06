from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


if TYPE_CHECKING:
    import _typeshed

type ServerType = Literal["granian", "uvicorn", "gunicorn"]


def root_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def absolute_path(
    *paths: _typeshed.StrPath | Path, base_path: _typeshed.StrPath | Path | None = None
) -> str:
    if base_path is None:
        base_path = root_dir()

    return os.path.join(base_path, *paths)


class DbConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env",
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
    connection_pool_size: int = 10
    connection_max_overflow: int = 90
    connection_pool_pre_ping: bool = True
    max_connections: int = 100

    def url(self) -> str:
        if self.driver.startswith("sqlite"):
            return f"{self.driver}:///{self.name}"

        return f"{self.driver}://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class ServerConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="SERVER_",
        extra="ignore",
    )
    host: str = "127.0.0.1"
    port: int = 9393
    timeout: int = 10
    type: ServerType = "granian"
    workers: int | Literal["auto"] = "auto"
    threads: int = 1
    log: bool = True


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="./.env",
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
        env_file="./.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="REDIS_",
        extra="ignore",
    )

    host: str = "127.0.0.1"
    port: int = 6379
    password: str | None = None


class Config(BaseSettings):
    app: AppConfig
    db: DbConfig
    server: ServerConfig
    redis: RedisConfig


def load_config(
    db: DbConfig | None = None,
    app: AppConfig | None = None,
    server: ServerConfig | None = None,
    redis: RedisConfig | None = None,
) -> Config:
    return Config(
        db=db or DbConfig(),
        app=app or AppConfig(),
        server=server or ServerConfig(),
        redis=redis or RedisConfig(),
    )

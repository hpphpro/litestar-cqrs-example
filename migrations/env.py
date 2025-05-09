import asyncio
from logging.config import fileConfig
from typing import Iterable

from alembic import context
from alembic.operations.ops import MigrationScript
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from src.config.core import load_config
from src.database.alchemy.entity import Entity


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Entity.metadata

if not (url := config.get_main_option("sqlalchemy.url")):
    url = load_config().db.url()


def add_number_to_migrations(
    context: MigrationContext,
    revision: str | None | Iterable[str | None],
    directives: list[MigrationScript],
) -> None:
    migration_script = directives[0]
    head_revision = ScriptDirectory.from_config(context.config).get_current_head()  # type: ignore
    if head_revision is None:
        new_rev_id = 1
    else:
        last_rev_id = int(head_revision.split("_")[0])
        new_rev_id = last_rev_id + 1

    migration_script.rev_id = f"{new_rev_id:05}_{migration_script.rev_id}"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=add_number_to_migrations,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,
        url=url
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()




def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    connectable = config.attributes.get("connection", None)

    if connectable:
        do_run_migrations(connectable)
    else:
        asyncio.run(run_async_migrations())





if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

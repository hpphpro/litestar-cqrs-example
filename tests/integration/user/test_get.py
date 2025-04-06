import uuid

from litestar import Litestar
from litestar.testing import AsyncTestClient

from src.api.v1.commands.user.create import CreateUser
from src.config.core import Config
from tests.integration.conftest import *  # noqa


async def test_get_many_by_offset_user_failed(
    client: AsyncTestClient[Litestar], app_config: Config
) -> None:
    response = await client.get(
        f"{app_config.app.root_path}/v1/users", params={"page": 1, "limit": 10}
    )

    data = response.json()

    assert response.status_code == 200 and data["total"] == 0 and len(data["items"]) == 0


async def test_get_one_user_success(client: AsyncTestClient[Litestar], app_config: Config) -> None:
    user = CreateUser(login="test", password="test_test")

    response = await client.post(f"{app_config.app.root_path}/v1/users", json=user.as_mapping())

    assert response.status_code == 201

    data = response.json()

    assert data["login"] == user.login
    assert data.get("password") is None

    response = await client.get(f"{app_config.app.root_path}/v1/users/{data['id']}")

    assert response.status_code == 200 and user.login == response.json()["login"]


async def test_get_one_user_failed(client: AsyncTestClient[Litestar], app_config: Config) -> None:
    response = await client.get(f"{app_config.app.root_path}/v1/users/{uuid.uuid4()}")

    assert response.status_code == 404


async def test_get_many_by_offset_user_success(
    client: AsyncTestClient[Litestar], app_config: Config
) -> None:
    for i in range(10):
        user = CreateUser(login=f"test_{i}", password="test_test")

        response = await client.post(f"{app_config.app.root_path}/v1/users", json=user.as_mapping())

        assert response.status_code == 201

        data = response.json()

        assert data["login"] == user.login
        assert data.get("password") is None

    response = await client.get(
        f"{app_config.app.root_path}/v1/users", params={"page": 1, "limit": 10}
    )

    data = response.json()

    assert response.status_code == 200 and data["total"] == 10 and len(data["items"]) == 10

    response = await client.get(
        f"{app_config.app.root_path}/v1/users", params={"page": 2, "limit": 10}
    )

    data = response.json()

    assert response.status_code == 200 and data["total"] == 10 and len(data["items"]) == 0

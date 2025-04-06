from tests.integration.conftest import *  # noqa

from litestar import Litestar
from litestar.testing import AsyncTestClient
from src.api.v1.commands.user.update import UpdateUser
from src.api.v1.commands.user.create import CreateUser

from src.config.core import Config


async def test_user_update_success(client: AsyncTestClient[Litestar], app_config: Config) -> None:
    user = CreateUser(login="test", password="test_test")

    response = await client.post(f"{app_config.app.root_path}/v1/users", json=user.as_mapping())

    assert response.status_code == 201

    data = response.json()

    assert data["login"] == user.login
    assert data.get("password") is None

    update = UpdateUser(login="new_test")

    response = await client.patch(
        f"{app_config.app.root_path}/v1/users/{data['id']}", json=update.as_mapping()
    )

    assert response.status_code == 200 and response.json()["status"]

    # ensure
    response = await client.get(f"{app_config.app.root_path}/v1/users/{data['id']}")

    assert response.status_code == 200 and response.json()["login"] == update.login


async def test_user_update_same_login_failed(
    client: AsyncTestClient[Litestar], app_config: Config
) -> None:
    user = CreateUser(login="test", password="test_test")

    response = await client.post(f"{app_config.app.root_path}/v1/users", json=user.as_mapping())

    assert response.status_code == 201

    data = response.json()

    assert data["login"] == user.login
    assert data.get("password") is None

    user2 = CreateUser(login="test2", password="test_test")

    response = await client.post(f"{app_config.app.root_path}/v1/users", json=user2.as_mapping())

    assert response.status_code == 201

    data = response.json()

    assert data["login"] == user2.login
    assert data.get("password") is None

    update = UpdateUser(login="test")

    response = await client.patch(
        f"{app_config.app.root_path}/v1/users/{data['id']}", json=update.as_mapping()
    )

    assert response.status_code == 409 or not response.json()["status"]

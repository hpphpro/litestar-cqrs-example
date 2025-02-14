from litestar import Router

from src.api.v1.endpoints.public.user import UserController


def setup_v1_public_controllers(app: Router) -> None:
    app.register(UserController)

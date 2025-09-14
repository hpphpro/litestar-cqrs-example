from litestar import Router

from backend.http.v1.controllers.public.auth import AuthController
from backend.http.v1.controllers.public.user import UserController


def setup_v1_public_controllers(router: Router) -> None:
    public_router = Router(path="/public", route_handlers=[UserController, AuthController])

    router.register(public_router)

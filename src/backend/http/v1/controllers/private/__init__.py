from litestar import Router

from .middlewares.auth import JWTAuthMiddleware
from .rbac import RbacController
from .user import UserController


def setup_v1_private_controllers(router: Router) -> None:
    private_router = Router(
        path="/private",
        route_handlers=[UserController, RbacController],
        middleware=[JWTAuthMiddleware()],
    )

    router.register(private_router)

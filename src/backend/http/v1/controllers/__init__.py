from litestar import Router

from .private import setup_v1_private_controllers
from .public import setup_v1_public_controllers


def setup_controllers(router: Router) -> None:
    setup_v1_private_controllers(router)
    setup_v1_public_controllers(router)

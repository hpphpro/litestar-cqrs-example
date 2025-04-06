from litestar import Router

from src.api.common import tools
from src.api.v1.dependencies import setup_v1_dependencies
from src.api.v1.endpoints import setup_controllers
from src.config.core import Config


def init_v1_router(*sub_routers: Router, path: str = "/v1", config: Config) -> tools.RouterState:
    router = Router(path, route_handlers=sub_routers)

    setup_controllers(router)
    state = setup_v1_dependencies(router, config)

    return tools.RouterState(router=router, state=state)

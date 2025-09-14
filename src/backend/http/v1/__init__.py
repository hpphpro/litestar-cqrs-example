from litestar import Router

from backend.http.healthcheck import healthcheck_endpoint
from backend.http.v1.controllers import setup_controllers


def init_v1_router(*sub_routers: Router, path: str = "/v1") -> Router:
    router = Router(path, route_handlers=sub_routers)
    router.register(healthcheck_endpoint)
    setup_controllers(router)

    return router

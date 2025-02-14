from litestar import Router

from src.api.v1.endpoints.healthcheck import healthcheck_endpoint
from src.api.v1.endpoints.public import setup_v1_public_controllers


def setup_controllers(app: Router) -> None:
    app.register(healthcheck_endpoint)
    setup_v1_public_controllers(app)

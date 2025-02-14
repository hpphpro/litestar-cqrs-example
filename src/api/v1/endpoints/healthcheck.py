from litestar import MediaType, Request, get, status_codes
from litestar.datastructures import State

from src.api.v1 import dto
from src.api.v1.queries import QueryBus


@get(
    "/healthcheck",
    media_type=MediaType.JSON,
    tags=["healthcheck"],
    status_code=status_codes.HTTP_200_OK,
)
async def healthcheck_endpoint(
    query_bus: QueryBus, request: Request[None, None, State]
) -> dto.healthcheck.HealthCheck:
    return dto.healthcheck.HealthCheck(ok=True)

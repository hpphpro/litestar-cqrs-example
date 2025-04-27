from litestar import MediaType, get, status_codes

from src.api.v1 import dto


@get(
    "/healthcheck",
    media_type=MediaType.JSON,
    tags=["healthcheck"],
    status_code=status_codes.HTTP_200_OK,
)
async def healthcheck_endpoint() -> dto.healthcheck.HealthCheck:
    return dto.healthcheck.HealthCheck(ok=True)

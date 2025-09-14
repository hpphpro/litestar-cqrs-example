from litestar import MediaType, get, status_codes

from backend.http.common.dto import HealthCheck


@get(
    "/healthcheck",
    media_type=MediaType.JSON,
    tags=["healthcheck"],
    status_code=status_codes.HTTP_200_OK,
)
async def healthcheck_endpoint() -> HealthCheck:
    return HealthCheck(status=True)

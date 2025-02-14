import logging
from collections.abc import Callable
from functools import partial
from typing import Any

from litestar import MediaType, Request, Response, Router
from litestar import status_codes as status
from litestar.types import ExceptionHandlersMap

import src.common.exceptions as exc


log = logging.getLogger(__name__)

JsonResponse = Response[dict[str, Any]]
BasicRequest = Request[Any, Any, Any]


def current_common_exc_handlers() -> ExceptionHandlersMap:
    return {
        exc.UnAuthorizedError: error_handler(status.HTTP_401_UNAUTHORIZED),
        exc.NotFoundError: error_handler(status.HTTP_404_NOT_FOUND),
        exc.ConflictError: error_handler(status.HTTP_409_CONFLICT),
        exc.ServiceNotImplementedError: error_handler(status.HTTP_501_NOT_IMPLEMENTED),
        exc.ServiceUnavailableError: error_handler(status.HTTP_503_SERVICE_UNAVAILABLE),
        exc.BadRequestError: error_handler(status.HTTP_400_BAD_REQUEST),
        exc.ForbiddenError: error_handler(status.HTTP_403_FORBIDDEN),
        exc.TooManyRequestsError: error_handler(status.HTTP_429_TOO_MANY_REQUESTS),
        exc.AppException: error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
        exc.RequestTimeoutError: error_handler(status.HTTP_408_REQUEST_TIMEOUT),
    }


def setup_common_exception_handlers(router: Router) -> None:
    router.exception_handlers.update(current_common_exc_handlers())


def error_handler(
    status_code: int,
) -> Callable[..., JsonResponse]:
    return partial(app_error_handler, status_code=status_code)


def app_error_handler(
    request: BasicRequest, exc: exc.AppException, status_code: int
) -> JsonResponse:
    return handle_error(
        request,
        exc=exc,
        status_code=status_code,
    )


def handle_error(
    _: BasicRequest,
    exc: exc.AppException,
    status_code: int,
) -> JsonResponse:
    log.error(f"Handle error: {type(exc).__name__} -> {exc.args}")

    return JsonResponse(**exc.as_dict(), status_code=status_code, media_type=MediaType.JSON)

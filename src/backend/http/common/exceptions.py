import logging
from collections.abc import Callable
from functools import partial
from typing import Any

from litestar import MediaType, Request, Response, Router
from litestar import status_codes as status
from litestar.types import ExceptionHandlersMap

import backend.app.contracts.exceptions as app_exc


log = logging.getLogger(__name__)

JsonResponse = Response[dict[str, Any]]
BasicRequest = Request[Any, Any, Any]


def exc_handlers() -> ExceptionHandlersMap:
    return {
        app_exc.UnAuthorizedError: error_handler(status.HTTP_401_UNAUTHORIZED),
        app_exc.NotFoundError: error_handler(status.HTTP_404_NOT_FOUND),
        app_exc.ConflictError: error_handler(status.HTTP_409_CONFLICT),
        app_exc.ServiceNotImplementedError: error_handler(status.HTTP_501_NOT_IMPLEMENTED),
        app_exc.ServiceUnavailableError: error_handler(status.HTTP_503_SERVICE_UNAVAILABLE),
        app_exc.BadRequestError: error_handler(status.HTTP_400_BAD_REQUEST),
        app_exc.ForbiddenError: error_handler(status.HTTP_403_FORBIDDEN),
        app_exc.TooManyRequestsError: error_handler(status.HTTP_429_TOO_MANY_REQUESTS),
        app_exc.AppError: error_handler(status.HTTP_500_INTERNAL_SERVER_ERROR),
        app_exc.RequestTimeoutError: error_handler(status.HTTP_408_REQUEST_TIMEOUT),
        app_exc.UnprocessableEntityError: error_handler(status.HTTP_422_UNPROCESSABLE_ENTITY),
    }


def setup_exc_handlers(router: Router) -> None:
    router.exception_handlers.update(exc_handlers())


def error_handler(
    status_code: int,
) -> Callable[..., JsonResponse]:
    return partial(app_error_handler, status_code=status_code)


def app_error_handler(
    request: BasicRequest,
    exc: app_exc.AppError,
    status_code: int,
) -> JsonResponse:
    return handle_error(
        request,
        exc=exc,
        status_code=status_code,
    )


def handle_error(
    _: BasicRequest,
    exc: app_exc.AppError,
    status_code: int,
) -> JsonResponse:
    log.error("Handle error: %s -> %s", type(exc).__name__, exc.args)

    return JsonResponse(
        **exc.as_dict(),
        status_code=status_code,
        media_type=MediaType.JSON,
    )

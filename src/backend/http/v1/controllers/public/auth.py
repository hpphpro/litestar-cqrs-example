from typing import Annotated

from litestar import Controller, MediaType, Request, Response, post, status_codes
from litestar.datastructures import Cookie, State
from litestar.middleware.rate_limit import RateLimitConfig
from litestar.params import Body

from backend.app import dto
from backend.app.contracts import exceptions as exc
from backend.app.contracts.auth import JwtToken
from backend.app.use_cases import commands
from backend.http.common import docs


class AuthController(Controller):
    path = "/auth"
    tags = ["auth"]

    @post(
        "/login",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.InternalServer.to_spec() | docs.TooManyRequests.to_spec(),
        middleware=[RateLimitConfig(("minute", 5)).middleware],
    )
    async def login_endpoint(
        self,
        data: Annotated[
            dto.user.LoginUser,
            Body(title="Login user", description="`Login user`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[None, None, State],
    ) -> Response[JwtToken]:
        result = await command_bus.send_unwrapped(
            request.state.ctx, commands.auth.login.LoginUserCommand(data=data)
        )

        return Response(
            content=result.access_token,
            media_type=MediaType.JSON,
            status_code=status_codes.HTTP_200_OK,
            cookies=[
                Cookie(
                    "refresh",
                    value=result.refresh_token.token,
                    httponly=True,
                    max_age=result.expires_in,
                    secure=True,
                    samesite="none",
                )
            ],
        )

    @post(
        "/logout",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.InternalServer.to_spec() | docs.TooManyRequests.to_spec(),
        middleware=[RateLimitConfig(("minute", 5)).middleware],
    )
    async def logout_endpoint(
        self,
        data: Annotated[
            dto.user.LogoutUser,
            Body(title="Logout user", description="`Logout user`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[None, None, State],
    ) -> Response[dto.Status]:
        token = request.cookies.get("refresh", "")
        if not token and (auth := request.headers.get("Authorization", "")):
            scheme, _, token = auth.partition(" ")
            if scheme.lower() != "bearer":
                raise exc.UnAuthorizedError("Invalid token provided")

        result = await command_bus.send_unwrapped(
            request.state.ctx,
            commands.auth.logout.LogoutUserCommand(data=data, token=JwtToken(token)),
        )

        return Response(
            content=result,
            media_type=MediaType.JSON,
            status_code=status_codes.HTTP_200_OK,
            cookies=[Cookie("refresh", max_age=0, expires=0)],
        )

    @post(
        "/refresh",
        media_type=MediaType.JSON,
        status_code=status_codes.HTTP_200_OK,
        responses=docs.InternalServer.to_spec() | docs.TooManyRequests.to_spec(),
        middleware=[RateLimitConfig(("minute", 5)).middleware],
    )
    async def refresh_endpoint(
        self,
        data: Annotated[
            dto.user.RefreshUser,
            Body(title="Refresh user", description="`Refresh user`"),
        ],
        command_bus: commands.CommandBus,
        request: Request[None, None, State],
    ) -> Response[JwtToken]:
        token = request.cookies.get("refresh", "")
        if not token and (auth := request.headers.get("Authorization", "")):
            scheme, _, token = auth.partition(" ")
            if scheme.lower() != "bearer":
                raise exc.UnAuthorizedError("Invalid token provided")

        result = await command_bus.send_unwrapped(
            request.state.ctx,
            commands.auth.refresh.RefreshUserCommand(data=data, token=JwtToken(token)),
        )

        return Response(
            content=result.access_token,
            media_type=MediaType.JSON,
            status_code=status_codes.HTTP_200_OK,
            cookies=[
                Cookie(
                    "refresh",
                    value=result.refresh_token.token,
                    httponly=True,
                    max_age=result.expires_in,
                    secure=True,
                    samesite="none",
                )
            ],
        )

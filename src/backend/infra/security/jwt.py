from __future__ import annotations

import base64
import hashlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from uuid_utils import uuid4

from backend.app.contracts.auth import (
    AUTH_KEY_PREFIX,
    Fingerprint,
    JwtToken,
    TokenClaims,
    TokenPair,
    TokenType,
)
from backend.app.contracts.shared_lock import SharedLock
from backend.infra.cache.redis import RedisCache
from backend.infra.shared.result import as_result
from config.core import SecurityConfig


def _try_decode(value: str) -> str:
    value = "".join(value.strip().split("\n"))
    try:
        return base64.b64decode(value).decode()
    except Exception:  # noqa: BLE001
        return value


class JwtImpl:
    __slots__ = (
        "_access_expires",
        "_algorithm",
        "_public_key",
        "_refresh_expires",
        "_secret_key",
    )

    def __init__(
        self,
        algorithm: str,
        public_key: str,
        secret_key: str,
        access_expires: float,
        refresh_expires: float,
    ) -> None:
        self._algorithm = algorithm
        self._public_key = _try_decode(public_key)
        self._secret_key = _try_decode(secret_key)
        self._access_expires = access_expires
        self._refresh_expires = refresh_expires

    @classmethod
    def from_config(cls, config: SecurityConfig) -> JwtImpl:
        return cls(
            algorithm=config.algorithm,
            public_key=config.public_key,
            secret_key=config.secret_key,
            access_expires=config.access_token_expire_seconds,
            refresh_expires=config.refresh_token_expire_seconds,
        )

    def _encode(
        self,
        sub: str,
        typ: TokenType,
        iat: datetime,
        ttl: timedelta,
        jti: str | None = None,
        iss: str | None = None,
        aud: str | None = None,
        **extra: dict[str, Any],
    ) -> str:
        payload = {
            "sub": sub,
            "exp": iat + ttl,
            "iat": iat,
            "typ": typ,
        }
        if jti:
            payload["jti"] = jti
        if iss:
            payload["iss"] = iss
        if aud:
            payload["aud"] = aud
        if extra:
            payload["extra"] = extra

        return jwt.encode(
            payload,
            self._secret_key,
            algorithm=self._algorithm,
        )

    @as_result(is_async=False)
    def issue_pair(
        self,
        sub: str,
        *,
        ttl: int | timedelta | None = None,
        refresh_ttl: int | timedelta | None = None,
        jti: str | None = None,
        iss: str | None = None,
        aud: str | None = None,
        **extra: Any,
    ) -> TokenPair:
        if ttl is not None:
            ttl = timedelta(seconds=ttl) if isinstance(ttl, int) else ttl
        else:
            ttl = timedelta(seconds=self._access_expires)

        if refresh_ttl is not None:
            refresh_ttl = (
                timedelta(seconds=refresh_ttl) if isinstance(refresh_ttl, int) else refresh_ttl
            )
        else:
            refresh_ttl = timedelta(seconds=self._refresh_expires)

        now = datetime.now(UTC)

        access_token = self._encode(sub, "access", now, ttl, iss, aud, **extra)
        refresh_token = self._encode(sub, "refresh", now, refresh_ttl, jti, iss, aud, **extra)

        return TokenPair(
            JwtToken(access_token),
            JwtToken(refresh_token),
            int(refresh_ttl.total_seconds()),
        )

    @as_result(is_async=False)
    def verify(self, token: str, iss: str | None = None, aud: str | None = None) -> TokenClaims:
        return TokenClaims(
            **jwt.decode(
                token, self._public_key, algorithms=[self._algorithm], issuer=iss, audience=aud
            )
        )


class RefreshStoreImpl:
    __slots__ = (
        "_cache",
        "_jwt",
        "_lock",
    )

    def __init__(self, cache: RedisCache, jwt: JwtImpl, lock: type[SharedLock]) -> None:
        self._cache = cache
        self._jwt = jwt
        self._lock = lock

    @as_result()
    async def make_token(self, user_id: uuid.UUID, fingerprint: Fingerprint) -> TokenPair:
        key = AUTH_KEY_PREFIX.format(user_id=user_id.hex)
        jti = uuid4().hex

        pair = self._jwt.issue_pair(user_id.hex, jti=jti).unwrap()
        hashed_pair = (
            f"{jti}:{hashlib.sha256(f'{fingerprint}:{pair.refresh_token}'.encode()).hexdigest()}"
        )

        await self._cache.set_list(key, hashed_pair)

        return pair

    @as_result()
    async def rotate(self, fingerprint: Fingerprint, token: JwtToken) -> TokenPair | None:
        claims = self._get_verified_claims(token)

        key = AUTH_KEY_PREFIX.format(user_id=claims.sub)

        async with self._lock(f"lock:{key}", timeout=15):
            hashed_pair = self._get_hashed_pair(claims, fingerprint, token)

            if not any(pair == hashed_pair for pair in await self._cache.get_list(key)):
                await self._cache.delete(key)
                return None

            await self._cache.discard(key, hashed_pair)

            result = self._jwt.issue_pair(claims.sub, jti=claims.jti or uuid4().hex).unwrap()

            await self._cache.set_list(
                key,
                self._get_hashed_pair(claims, fingerprint, result.refresh_token),
                expire=result.expires_in,
            )

            return result

    @as_result()
    async def revoke(self, fingerprint: Fingerprint, token: JwtToken) -> bool:
        claims = self._get_verified_claims(token)

        key = AUTH_KEY_PREFIX.format(user_id=claims.sub)
        hashed_pair = self._get_hashed_pair(claims, fingerprint, token)

        if any(pair == hashed_pair for pair in await self._cache.get_list(key)):
            await self._cache.discard(key, hashed_pair)
            return True

        return False

    def _get_verified_claims(self, token: JwtToken) -> TokenClaims:
        return (
            self._jwt.verify(token.token)
            .and_then(lambda c: c if c.typ == "refresh" else None)
            .unwrap()
        )

    def _get_hashed_pair(
        self, claims: TokenClaims, fingerprint: Fingerprint, token: JwtToken
    ) -> str:
        hashed_pair = hashlib.sha256(f"{fingerprint}:{token}".encode()).hexdigest()

        return hashed_pair if not claims.jti else f"{claims.jti}:{hashed_pair}"

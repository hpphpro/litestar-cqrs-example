from dataclasses import dataclass
from typing import Any, override

from src.api.common.interfaces.event import Event, EventHandler
from src.api.common.tools import msgspec_encoder


try:
    from nats.aio.client import Client
    from nats.js import JetStreamContext
except ImportError as e:
    raise RuntimeError(
        f"Required package not found: {e.name}. "
        f"To use nats-bus, ensure you have installed the 'nats-py' package. "
        "You can install it using: pip install nats-py"
    ) from e


@dataclass
class NatsBaseEventHandler(EventHandler[Event]):
    client: Client

    @override
    async def __call__(self, event: Event, /, **kw: Any) -> None:
        await self.client.publish(
            event.name,
            payload=msgspec_encoder(event).encode(),
            reply=kw.pop("reply", self.client.new_inbox()),
            **kw,
        )


@dataclass
class NatsJsEventHandler(EventHandler[Event]):
    js: JetStreamContext

    @override
    async def __call__(self, event: Event, /, **kw: Any) -> None:
        await self.js.publish(event.name, payload=msgspec_encoder(event).encode(), **kw)

from dataclasses import dataclass
from typing import Any, override

from backend.app.bus.interfaces.event import Event, EventHandler
from backend.shared.types import JsonDumps


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
    encoder: JsonDumps

    @override
    async def __call__(self, event: Event, /, **kw: Any) -> None:
        await self.client.publish(
            event.name(),
            payload=self.encoder(event).encode(),
            reply=kw.pop("reply", self.client.new_inbox()),
            **kw,
        )


@dataclass
class NatsJsEventHandler(EventHandler[Event]):
    js: JetStreamContext
    encoder: JsonDumps

    @override
    async def __call__(self, event: Event, /, **kw: Any) -> None:
        await self.js.publish(event.name(), payload=self.encoder(event).encode(), **kw)

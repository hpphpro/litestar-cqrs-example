import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, MappedAsDataclass, declarative_mixin, mapped_column
from uuid_utils import uuid7


@declarative_mixin
class WithIDMixin(MappedAsDataclass, init=False):
    id: Mapped[int] = mapped_column(sa.Integer, primary_key=True)


@declarative_mixin
class WithBigIDMixin(MappedAsDataclass, init=False):
    id: Mapped[int] = mapped_column(sa.BigInteger, primary_key=True)


@declarative_mixin
class WithSmallIDMixin(MappedAsDataclass, init=False):
    id: Mapped[int] = mapped_column(sa.SmallInteger, primary_key=True)


@declarative_mixin
class WithUUIDMixin(MappedAsDataclass, init=False):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        insert_default=uuid7,
        server_default=sa.func.uuid_generate_v7(),
    )

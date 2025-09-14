from datetime import UTC, datetime
from functools import partial

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, MappedAsDataclass, declarative_mixin, mapped_column


@declarative_mixin
class WithTimeMixin(MappedAsDataclass, init=False):
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        insert_default=partial(datetime.now, UTC),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        onupdate=func.now(),
        server_default=func.now(),
        insert_default=partial(datetime.now, UTC),
    )


@declarative_mixin
class WithDeletedTimeMixin(WithTimeMixin):
    deleted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

import enum
from typing import Literal, TypedDict

import sqlalchemy.sql.selectable


type CursorIntegerType = Literal["integer"]
type CursorUUIDType = Literal["uuid"]
type CursorType = Literal[CursorUUIDType, CursorIntegerType]


class UnsetType(enum.Enum):
    UNSET = enum.auto()


class OnUpdateType(TypedDict, total=False):
    nowait: bool
    read: bool
    of: sqlalchemy.sql.selectable._ForUpdateOfArgument
    skip_locked: bool
    key_share: bool

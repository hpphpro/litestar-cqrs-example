import uuid
from datetime import datetime

from src.api.common import dto


class User(dto.BaseDTO):
    id: uuid.UUID
    login: str
    created_at: datetime

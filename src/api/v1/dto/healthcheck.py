from src.api.common import dto


class HealthCheck(dto.BaseDTO):
    ok: bool

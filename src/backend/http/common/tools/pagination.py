def page_to_offset(page: int, limit: int) -> int:
    if page <= 0:
        return 0

    return (page - 1) * limit

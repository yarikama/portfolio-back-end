def offset_pagination(offset: int, limit: int, total: int) -> dict:
    """Return offset-based pagination metadata.

    Args:
        offset: Number of items to skip
        limit: Maximum number of items to return
        total: Total number of items available

    Returns:
        dict with total, limit, offset, hasMore
    """
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "hasMore": offset + limit < total,
    }

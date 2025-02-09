def not_none[T](value: T | None) -> T:
    if value is None:
        raise ValueError("Value cannot be None.")
    return value

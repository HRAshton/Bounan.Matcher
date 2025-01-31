from typing import TypeVar

T = TypeVar('T')


def not_null(value: T | None) -> T:
    if value is None:
        raise ValueError("Value is None")

    return value

from typing import Any

class BinanceAPIException(Exception):
    code: int
    message: str

    def __init__(self, *args: Any, **kwargs: Any) -> None: ...
    def __str__(self) -> str: ...

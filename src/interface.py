from typing import Any, Protocol
from dataclasses import dataclass
from datetime import datetime

@dataclass
class IdempotencyKey: 
    key: str 
    fingerprint: str
    status: str 
    created_at: datetime
    updated_at: datetime
    result_data: bytes | None = None
    result_status: int | None = None
    result_error: str | None = None
    

class IdempotencyProtocol(Protocol):
    def __init__(self, key: str, fingerprint: str) -> None:
        self.key = key
        self.fingerprint = fingerprint

    def get_key(self) -> str:
        pass


    
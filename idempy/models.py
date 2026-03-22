from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from typing import Any

class BeginAction(str, Enum):
    INVALID_REQUEST = "invalid_request"
    PROCESS = "process"
    REPLAY = "replay"
    IN_PROGRESS = "in_progress"
    CONFLICT = "conflict"
    SUCCESS = "success"
    FAILED = "failed"
    NOT_FOUND = "not_found"

class Status(str, Enum):
    PENDING = 'pending'
    SUCCESS = 'success'
    FAILED = 'failed'
    NOT_FOUND = 'not_found'

class State(str, Enum):
    CONFLICT = 'conflict'
    IN_PROGRESS = 'in_progress'
    REPLAY = 'replay'
    PROCESS = 'process'


class CompleteAction(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class FailAction(str, Enum):
    FAILED = "failed"


class ReplayAction(str, Enum):
    INVALID_REQUEST = "invalid_request"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    SUCCESS = "success"


class GetStatusAction(str, Enum):
    NOT_FOUND = "not_found"
    SUCCESS = "success"


class DeleteAction(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"


@dataclass(frozen=True, slots=True)
class IdempotencyKey:
    key: str
    fingerprint: str
    status: str
    created_at: datetime
    updated_at: datetime
    result_data: bytes | None = None
    result_status: int | None = None
    result_error: str | None = None

@dataclass(frozen=True, slots=True)
class Request:
    idempotency_key: str
    fingerprint: str
    method: str
    path: str
    url: str
    headers: dict[str, str]
    body: bytes
    query_params: dict[str, str]
    path_params: dict[str, str]
    cookies: dict[str, str]
    json: dict[str, Any]
    store: str = "memory"


@dataclass(slots=True)
class IdempotencyRecord:
    status: Status
    idempotency_key: IdempotencyKey
    request: Request
    result: Any = None
    error: Exception | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

@dataclass(frozen=True, slots=True)
class BeginResult:
    action: BeginAction
    record: IdempotencyRecord | None = None
    message: str | None = None

@dataclass(frozen=True, slots=True)
class CompleteResult:
    action: CompleteAction
    record: IdempotencyRecord | None = None
    message: str | None = None

@dataclass(frozen=True, slots=True)
class FailResult:
    action: FailAction
    record: IdempotencyRecord | None = None
    message: str | None = None

@dataclass(frozen=True, slots=True)
class ReplayResult:
    action: ReplayAction
    record: IdempotencyRecord | None = None
    message: str | None = None
  
@dataclass(frozen=True, slots=True)
class GetStatusResult:
    action: GetStatusAction
    record: IdempotencyRecord | None = None
    message: str | None = None

@dataclass(frozen=True, slots=True)
class DeleteResult:
    action: DeleteAction
    record: IdempotencyRecord | None = None
    message: str | None = None

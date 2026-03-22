import hashlib
from datetime import datetime
from typing import Any

from idempy.memory import MemoryStore
from idempy.models import (
    BeginAction,
    BeginResult,
    IdempotencyKey,
    IdempotencyRecord,
    ReplayAction,
    ReplayResult,
    Request,
    Status,
)
from idempy.stores import Stores

DEFAULT_SETTINGS = {
    'idempy_key_prefix': 'idempotency_key_',
    'datetime_class': datetime,
    'stores': {
        'memory': MemoryStore(),
    },
    'default_store': 'memory',
}


class Core:
    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        merged = {**DEFAULT_SETTINGS, **(settings or {})}
        self.settings = merged
        self.stores = Stores(merged['stores'], default=merged.get('default_store'))

    def validate_request(self, request: Request | dict[str, Any]) -> bool:
        if request is None:
            return False
        if hasattr(request, 'idempotency_key'):
            key = request.idempotency_key or (request.headers or {}).get('Idempotency-Key')
        else:
            key = request.get('idempotency_key') or (request.get('headers') or {}).get('Idempotency-Key')
        return bool(key and str(key).strip())

    def validate_fingerprint(self, fingerprint: str) -> bool:
        if not isinstance(fingerprint, str) or not fingerprint:
            return False
        return bool(fingerprint.strip())

    def build_fingerprint(self, request: Request | dict[str, Any]) -> str:
        raw = request.fingerprint if hasattr(request, 'fingerprint') else request.get('fingerprint', '')
        return hashlib.sha256(str(raw).encode()).hexdigest()

    def get_store(self, name: str | None = None) -> "BaseStore":
        from idempy.base import BaseStore
        return self.stores.get(name or self.settings.get('default_store'))

    def build_idempotency_key(self, request: Request) -> str:
        prefix = self.settings.get('idempy_key_prefix', 'idempotency_key_')
        return f"{prefix}{request.idempotency_key}"

    def _to_request(self, request: Request | dict[str, Any]) -> Request:
        if isinstance(request, Request):
            return request
        defaults = {
            "method": "",
            "path": "",
            "url": "",
            "headers": request.get("headers", {}),
            "body": request.get("body", b""),
            "query_params": request.get("query_params", {}),
            "path_params": request.get("path_params", {}),
            "cookies": request.get("cookies", {}),
            "json": request.get("json", {}),
        }
        return Request(
            idempotency_key=str(request.get("idempotency_key", "")),
            fingerprint=str(request.get("fingerprint", "")),
            **defaults,
        )

    def begin(self, request: Request | dict[str, Any]) -> BeginResult:
        req = self._to_request(request) if isinstance(request, dict) else request
        if not self.validate_request(req):
            return BeginResult(action=BeginAction.INVALID_REQUEST, message='Invalid request')

        idempotency_key = self.build_idempotency_key(req)
        fingerprint = self.build_fingerprint(req)
        store = self.get_store(getattr(req, 'store', None))

        existing = store.get(idempotency_key)
        if existing is not None:
            if existing.fingerprint == fingerprint:
                return BeginResult(
                    action=BeginAction.REPLAY,
                    record=self._key_to_record(existing, req),
                    message='Replay',
                )
            return BeginResult(action=BeginAction.CONFLICT, message='Conflict')

        store.create_in_progress(idempotency_key, fingerprint)
        now = datetime.now()
        key_obj = IdempotencyKey(
            key=idempotency_key,
            fingerprint=fingerprint,
            status=Status.PENDING,
            created_at=now,
            updated_at=now,
        )
        record = IdempotencyRecord(
            status=Status.PENDING,
            idempotency_key=key_obj,
            request=req,
        )
        return BeginResult(action=BeginAction.SUCCESS, record=record, message='Success')

    def _key_to_record(self, key: IdempotencyKey, request: Request) -> IdempotencyRecord:
        return IdempotencyRecord(
            status=Status(key.status) if key.status in Status.__members__ else Status.PENDING,
            idempotency_key=key,
            request=request,
        )

    def complete(
        self,
        record: IdempotencyRecord,
        result_data: bytes,
        result_status: int,
    ) -> Status:
        store = self.get_store(getattr(record.request, 'store', None))
        store.mark_completed(
            record.idempotency_key.key,
            record.idempotency_key.fingerprint,
            result_data,
            result_status,
        )
        record.status = Status.SUCCESS
        record.result = result_data
        record.updated_at = datetime.now()
        return Status.SUCCESS

    def fail(self, record: IdempotencyRecord, result_error: str) -> Status:
        store = self.get_store(getattr(record.request, 'store', None))
        store.mark_failed(
            record.idempotency_key.key,
            record.idempotency_key.fingerprint,
            result_error,
        )
        record.status = Status.FAILED
        record.error = RuntimeError(result_error)
        record.updated_at = datetime.now()
        return Status.FAILED

    def replay(self, request: Request) -> ReplayResult:
        if not self.validate_request(request):
            return ReplayResult(
                action=ReplayAction.INVALID_REQUEST,
                message="Invalid request",
            )
        idempotency_key = self.build_idempotency_key(request)
        fingerprint = self.build_fingerprint(request)
        store = self.get_store(getattr(request, 'store', None))
        record = store.get(idempotency_key)
        if record is None:
            return ReplayResult(
                action=ReplayAction.NOT_FOUND,
                message="Replay not found",
            )
        if record.fingerprint != fingerprint:
            return ReplayResult(
                action=ReplayAction.CONFLICT,
                message="Fingerprint conflict",
            )
        return ReplayResult(
            action=ReplayAction.SUCCESS,
            record=self._key_to_record(record, request),
            message="Replay found",
        )

    def get_status(self, request: Request) -> Status:
        idempotency_key = self.build_idempotency_key(request)
        store = self.get_store(getattr(request, 'store', None))
        record = store.get(idempotency_key)
        if record is None:
            return Status.NOT_FOUND
        status_val = getattr(record.status, "value", record.status)
        try:
            return Status(status_val)
        except ValueError:
            return Status.PENDING

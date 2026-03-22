from datetime import datetime
from threading import Lock
from typing import Optional

from idempy.base import BaseStore
from idempy.models import IdempotencyKey, Status


class MemoryStore(BaseStore):
    """In-memory store for idempotency keys."""

    expiry_seconds: int = 60 * 60 * 24 * 30  # 30 days

    def __init__(self, clear: bool = False) -> None:
        self.store: dict[str, IdempotencyKey] = {}
        self._lock = Lock()
        if clear:
            self.store.clear()

    def _is_expired(self, record: IdempotencyKey) -> bool:
        if record.updated_at is None:
            return False
        elapsed = (datetime.now() - record.updated_at).total_seconds()
        return elapsed > self.expiry_seconds

    def get(self, key: str) -> Optional[IdempotencyKey]:
        with self._lock:
            record = self.store.get(key)
            if record is None:
                return None
            if self._is_expired(record):
                del self.store[key]
                return None
            return record

    def create_in_progress(self, key: str, fingerprint: str) -> bool:
        now = datetime.now()
        record = IdempotencyKey(
            key=key,
            fingerprint=fingerprint,
            status=Status.PENDING,
            created_at=now,
            updated_at=now,
        )
        with self._lock:
            if key in self.store:
                return False
            self.store[key] = record
        return True

    def mark_completed(
        self,
        key: str,
        fingerprint: str,
        result_data: bytes,
        result_status: int,
    ) -> bool:
        with self._lock:
            record = self.store.get(key)
            if record is None or record.fingerprint != fingerprint:
                return False
            now = datetime.now()
            updated = IdempotencyKey(
                key=key,
                fingerprint=fingerprint,
                status=Status.SUCCESS,
                created_at=record.created_at,
                updated_at=now,
                result_data=result_data,
                result_status=result_status,
            )
            self.store[key] = updated
        return True

    def mark_failed(self, key: str, fingerprint: str, result_error: str) -> bool:
        with self._lock:
            record = self.store.get(key)
            if record is None or record.fingerprint != fingerprint:
                return False
            now = datetime.now()
            updated = IdempotencyKey(
                key=key,
                fingerprint=fingerprint,
                status=Status.FAILED,
                created_at=record.created_at,
                updated_at=now,
                result_error=result_error,
            )
            self.store[key] = updated
        return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self.store:
                del self.store[key]
                return True
            return False

   
from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

import idempy.models as models


def test_begin_result_fields():
    r = models.BeginResult(
        action=models.BeginAction.SUCCESS,
        record=None,
        message=None,
    )
    assert r.action == models.BeginAction.SUCCESS
    assert r.record is None
    assert r.message is None


def test_begin_result_frozen():
    r = models.BeginResult(action=models.BeginAction.SUCCESS)
    with pytest.raises(FrozenInstanceError):
        r.action = models.BeginAction.FAILED  # type: ignore[misc]


def test_status_enum_values():
    assert models.Status.PENDING.value == "pending"
    assert models.Status.SUCCESS.value == "success"
    assert models.Status.FAILED.value == "failed"
    assert models.Status.NOT_FOUND.value == "not_found"


def test_state_enum_values():
    assert models.State.CONFLICT.value == "conflict"
    assert models.State.IN_PROGRESS.value == "in_progress"
    assert models.State.REPLAY.value == "replay"
    assert models.State.PROCESS.value == "process"


def test_replay_action_enum_values():
    assert models.ReplayAction.INVALID_REQUEST.value == "invalid_request"
    assert models.ReplayAction.SUCCESS.value == "success"


def test_request_defaults():
    req = models.Request(
        idempotency_key="k",
        fingerprint="f",
        method="GET",
        path="/",
        url="https://example.com",
        headers={},
        body=b"",
        query_params={},
        path_params={},
        cookies={},
        json={},
    )
    assert req.store == "memory"


def test_idempotency_key_and_record():
    now = datetime.now()
    key = models.IdempotencyKey(
        key="k",
        fingerprint="f",
        status="pending",
        created_at=now,
        updated_at=now,
    )
    req = models.Request(
        idempotency_key="k",
        fingerprint="f",
        method="GET",
        path="/",
        url="https://example.com",
        headers={},
        body=b"",
        query_params={},
        path_params={},
        cookies={},
        json={},
    )
    rec = models.IdempotencyRecord(
        status=models.Status.PENDING,
        idempotency_key=key,
        request=req,
    )
    assert rec.status == models.Status.PENDING
    assert rec.idempotency_key.key == "k"


def test_complete_fail_replay_result_frozen():
    with pytest.raises(FrozenInstanceError):
        models.CompleteResult(action=models.CompleteAction.SUCCESS).action = models.CompleteAction.FAILED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        models.FailResult(action=models.FailAction.FAILED).action = models.FailAction.FAILED  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        models.ReplayResult(action=models.ReplayAction.SUCCESS).action = models.ReplayAction.CONFLICT  # type: ignore[misc]

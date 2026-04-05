import pytest

from idempy.core import Core
from idempy.memory import MemoryStore
from idempy.models import BeginAction, ReplayAction, Request, Status


def make_request(idempotency_key: str, fingerprint: str) -> Request:
    return Request(
        idempotency_key=idempotency_key,
        fingerprint=fingerprint,
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


@pytest.fixture
def core():
    return Core()


def test_begin_complete_replay_and_status(core):
    req = make_request("pay-001", "fingerprint-abc")

    # First begin — should create a new in-progress record
    begin_result = core.begin(req)
    assert begin_result.action == BeginAction.SUCCESS
    assert begin_result.record is not None

    record = begin_result.record

    # Complete the operation
    core.complete(record, result_data=b'{"charged": true}', result_status=200)
    assert record.status == Status.SUCCESS

    # Same key + fingerprint should replay
    begin_again = core.begin(req)
    assert begin_again.action == BeginAction.REPLAY

    # replay() should return the stored record
    replay_result = core.replay(req)
    assert replay_result.action == ReplayAction.SUCCESS
    assert replay_result.record is not None

    # get_status() should reflect SUCCESS
    status = core.get_status(req)
    assert status == Status.SUCCESS


def test_begin_conflict(core):
    req = make_request("pay-002", "fingerprint-abc")
    req_different = make_request("pay-002", "fingerprint-xyz")

    begin_result = core.begin(req)
    assert begin_result.action == BeginAction.SUCCESS

    # Same key, different fingerprint — should conflict
    conflict_result = core.begin(req_different)
    assert conflict_result.action == BeginAction.CONFLICT


def test_begin_fail_and_status(core):
    req = make_request("pay-003", "fingerprint-abc")

    begin_result = core.begin(req)
    assert begin_result.action == BeginAction.SUCCESS

    record = begin_result.record
    core.fail(record, result_error="Payment gateway timeout")
    assert record.status == Status.FAILED

    status = core.get_status(req)
    assert status == Status.FAILED


def test_get_status_not_found(core):
    req = make_request("pay-does-not-exist", "fingerprint-abc")
    status = core.get_status(req)
    assert status == Status.NOT_FOUND


def test_replay_not_found(core):
    req = make_request("pay-never-started", "fingerprint-abc")
    result = core.replay(req)
    assert result.action == ReplayAction.NOT_FOUND

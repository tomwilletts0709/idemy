# idempy: lifecycle and roadmap

This document describes how the idempotency flow works today, what was added recently, and what to tackle next.

## What idempy does

The library tracks **idempotency keys** and **request fingerprints** so duplicate or retried work can be detected: same key + same fingerprint can be **replayed**; same key + different fingerprint is a **conflict**; new keys move through **in progress** → **completed** or **failed** in the backing store.

## Current lifecycle (implemented)

1. **`begin(request)`** — Validates presence of an idempotency key (from `Request` or a dict). Builds a prefixed storage key and a SHA-256 fingerprint from the request’s fingerprint field. Looks up the record in the selected store (`Request.store`, default `memory`).
   - **No record** — Creates an in-progress record in the store; returns `BeginAction.SUCCESS` with an `IdempotencyRecord`.
   - **Record exists, same fingerprint** — Returns `BeginAction.REPLAY` (safe to return stored outcome without re-running side effects).
   - **Record exists, different fingerprint** — Returns `BeginAction.CONFLICT`.
2. **`complete(record, result_data, result_status)`** — Persists success via `mark_completed` on the store and updates the in-memory `IdempotencyRecord`.
3. **`fail(record, result_error)`** — Persists failure via `mark_failed` and updates the record.
4. **`replay(request)`** — Loads by key; checks fingerprint; returns `ReplayResult` with actions such as `NOT_FOUND`, `CONFLICT`, or `SUCCESS`.
5. **`get_status(request)`** — Returns `Status` for the key, or `NOT_FOUND` if absent.

`begin` accepts either a **`Request`** dataclass or a **minimal dict** (filled via `_to_request` with empty defaults for HTTP fields).

## Recent additions

| Area | Notes |
|------|--------|
| **`Core`** | Merged settings, `Stores` integration, dict → `Request` coercion, REPLAY vs CONFLICT in `begin`, `complete` / `fail` wired to the store, `replay` and `get_status` aligned with stored `IdempotencyKey` status strings. |
| **`Stores`** | Named store registry with optional default (e.g. `memory`). |
| **`MemoryStore`** | Implements `BaseStore`: `get`, `create_in_progress`, `mark_completed`, `mark_failed`, `delete`, plus TTL-style expiry based on `updated_at`. |
| **`models`** | `Request.store`, result types (`BeginResult`, `ReplayResult`, etc.), action enums, `Status.NOT_FOUND`. |
| **`validator`** | Python 3.11–compatible `ValidatedField` / `non_empty` / `min_value` (no 3.12-only syntax). |
| **Packaging** | `pyproject.toml` with `[build-system]` so `pip install -e ".[dev]"` or `uv sync --extra dev` installs the package and fixes `ModuleNotFoundError: idempy` when running tests. |
| **Tests** | `test_validate_request`, `test_stores`, `test_validator` cover core validation, store registry, and descriptors. |

## How to run tests locally

From the repository root, after installing the project in editable mode:

```bash
uv sync --extra dev
uv run pytest
```

or:

```bash
pip install -e ".[dev]"
pytest
```

## What to do next (suggested order)

1. **README / structure** — Update the README’s project tree to include `stores.py`, `validator.py`, `tests/`, `docs/`, and `pyproject.toml`.
2. **Fingerprint semantics** — Today the fingerprint is a hash of `request.fingerprint` (often a precomputed client string). Document or add helpers to compute a canonical fingerprint from `method`, `path`, `body`, etc., so retries are stable across frameworks.
3. **`replay` and dict input** — `begin` accepts dicts; consider the same for `replay` / `get_status` via `_to_request` for consistency in scripts and tests.
4. **`_key_to_record` robustness** — Status mapping from stored strings to `Status` enum is intentionally conservative; add tests for completed/failed keys and edge cases.
5. **Persistence beyond memory** — Add a `BaseStore` implementation backed by Redis or SQLite for multi-process / durable deployments.
6. **Concurrency** — `MemoryStore` uses a lock per operation; document thread expectations; for distributed systems, rely on store atomicity (e.g. Redis `SET NX`).
7. **Integration examples** — Short examples for FastAPI/Flask/Django (middleware or dependency) showing `Idempotency-Key` header → `Request` → `Core.begin` → handler → `complete` / `fail`.
8. **Optional: CI** — GitHub Actions (or similar) running `pytest` on push/PR.
9. **Versioning** — When you publish to PyPI, add `README` as `readme` in `pyproject.toml` and tighten `requires-python` if you rely on newer syntax.

---

*Last updated to reflect the in-repo implementation; adjust this file as the API evolves.*

# idempy

A lightweight Python library for handling idempotent operations safely.

`idempy` helps prevent duplicate side effects when the same operation is retried. It is designed for backend systems where a request, job, or command may be sent more than once and must only be processed once.

## Why this exists

In real systems, duplicate requests happen all the time:

- clients retry after timeouts
- users double-submit forms
- webhooks are delivered more than once
- background jobs are replayed

Without idempotency, this can lead to duplicated side effects such as:

- charging a payment twice
- creating duplicate records
- processing the same event multiple times

`idempy` tracks **idempotency keys** and **request fingerprints**, stores execution state and results, and lets you **replay** a prior outcome when the same logical request arrives again.

## What works today

The **pure Python core** provides:

- **`Core`** — `begin`, `complete`, `fail`, `replay`, and `get_status` over a pluggable store
- **`Stores`** — named backends (e.g. `memory`) with a default
- **`MemoryStore`** — in-process implementation of `BaseStore` with TTL-style expiry
- **`Request`** / **`IdempotencyRecord`** — typed models and result enums (`BeginAction`, `ReplayResult`, `Status`, …)
- **`validator`** — optional `ValidatedField` helpers for boundary validation

See [docs/lifecycle.md](docs/lifecycle.md) for the full flow and roadmap.

## Requirements

- Python **3.11+**

## Installation

From a checkout of this repository:

```bash
pip install -e ".[dev]"
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv sync --extra dev
```

Install in editable mode so imports like `import idempy` work when running tests and local scripts.

## Quick usage

```python
from idempy import Core, BeginAction

core = Core()

req = {
    "idempotency_key": "pay-001",
    "fingerprint": "canonical-body-or-hash-from-client",
}

out = core.begin(req)
if out.action == BeginAction.INVALID_REQUEST:
    ...
elif out.action == BeginAction.REPLAY:
    # Same key + same fingerprint — use stored result, do not charge again
    ...
elif out.action == BeginAction.CONFLICT:
    # Same key, different fingerprint — reject
    ...
elif out.action == BeginAction.SUCCESS and out.record:
    # First time — run your side effect, then persist outcome
    core.complete(out.record, result_data=b"{}", result_status=200)
```

For production you will typically build a full **`Request`** (method, path, headers, body, etc.) and plug in a **durable store** (Redis, SQL) instead of the default in-memory backend.

## Development

Run tests from the repository root (after editable install):

```bash
pytest
```

## Project structure

```text
.
├── pyproject.toml      # packaging + dev deps (pytest)
├── uv.lock             # lockfile when using uv
├── docs/
│   └── lifecycle.md    # lifecycle + roadmap
├── idempy/
│   ├── __init__.py
│   ├── base.py         # BaseStore ABC
│   ├── core.py         # Core orchestration
│   ├── errors.py
│   ├── memory.py       # MemoryStore
│   ├── models.py
│   ├── stores.py       # Stores registry
│   └── validator.py
└── tests/
```

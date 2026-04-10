# idempy

A lightweight Python library for handling idempotent operations safely.

`idempy` prevents duplicate side effects when the same operation is retried. It tracks idempotency keys and request fingerprints, stores execution state, and replays prior outcomes for duplicate requests — so your side effects happen exactly once.

## Why this exists

Duplicate requests are a fact of distributed systems:

- clients retry after timeouts
- users double-submit forms
- webhooks are delivered more than once
- background jobs are replayed on worker failure

Without idempotency this leads to duplicate charges, duplicate records, and duplicate events. `idempy` gives you a structured, store-backed mechanism to detect and short-circuit these cases.

## How it works

Every operation follows the same lifecycle:

```
begin()  ──► NEW?     → do the work → complete() or fail()
         ──► REPLAY?  → return cached result (skip the work)
         ──► CONFLICT? → reject (same key, different request)
```

`begin()` is the gate. It creates a PENDING record on first call, or surfaces the prior outcome on retry. `complete()` and `fail()` seal the record. `replay()` and `get_status()` let you inspect it later.

## Quick start

```python
from idempy import Core, BeginAction

core = Core()

# Works with a plain dict or a fully typed Request object
result = core.begin({
    "idempotency_key": "pay-001",
    "fingerprint": "sha256-of-request-body",
})

if result.action == BeginAction.REPLAY:
    return result.record          # cached — do not charge again

if result.action == BeginAction.CONFLICT:
    raise Exception("409 Conflict")  # same key, different payload

if result.action == BeginAction.SUCCESS:
    response = charge_card()      # first time — do the work
    core.complete(result.record, result_data=response, result_status=200)
```

On retry with the same key and fingerprint:

```python
result = core.begin({"idempotency_key": "pay-001", "fingerprint": "sha256-of-request-body"})
assert result.action == BeginAction.REPLAY   # no double charge
```

## API

### `Core(settings=None)`

| Method | Description |
|---|---|
| `begin(request)` | Start an operation or surface a prior outcome |
| `complete(record, result_data, result_status)` | Mark as succeeded, store the response |
| `fail(record, result_error)` | Mark as failed, store the error |
| `replay(request)` | Fetch the stored result for a completed request |
| `get_status(request)` | Return the current `Status` for a key |

`begin()` accepts either a `Request` dataclass or a plain `dict` with at minimum `idempotency_key` and `fingerprint`.

### `BeginAction` values

| Value | Meaning |
|---|---|
| `SUCCESS` | New request — proceed with the operation |
| `REPLAY` | Seen before — return cached result |
| `CONFLICT` | Same key, different fingerprint — reject |
| `INVALID_REQUEST` | Missing or empty idempotency key |

### Settings

```python
core = Core(settings={
    "idempy_key_prefix": "myapp_",    # prefix for all stored keys
    "stores": {"memory": MemoryStore()},
    "default_store": "memory",
})
```

## Stores

`BaseStore` is an abstract interface. Implement it to plug in any backend.

| Store | Use case |
|---|---|
| `MemoryStore` | Single-process apps, testing, local dev |
| `RedisStore` | Multi-process, multi-server deployments |

`MemoryStore` is thread-safe with 30-day lazy TTL expiry. It does not survive process restarts.

`RedisStore` uses Redis hashes with native TTL and `SET NX` for atomic creation across multiple workers. Requires `pip install idempy[redis]`.

```python
from redis import Redis
from idempy import Core, RedisStore

store = RedisStore(Redis.from_url("redis://localhost:6379/0"))
core = Core(settings={"stores": {"redis": store}, "default_store": "redis"})
```

## Fingerprints

A fingerprint is a stable, canonical hash of the logical request — typically a SHA-256 of the HTTP method, path, and body. `idempy` compares fingerprints but does not compute them; the caller supplies one. This allows flexibility in what constitutes "the same request" for your domain.

```python
import hashlib

fingerprint = hashlib.sha256(b"POST /payments {amount: 100}").hexdigest()
```

## Validation

`ValidatedField` is an optional descriptor for adding cast-and-validate behaviour to class fields:

```python
from idempy import ValidatedField, non_empty, min_value

class Config:
    name    = ValidatedField(str, (non_empty,))
    retries = ValidatedField(int, (min_value(0),))
```

## Framework middleware

Drop-in middleware adapters gate every qualifying request through `Core.begin()` automatically — no per-handler code needed. Each adapter auto-computes the fingerprint from the HTTP method, path, and body.

### Flask

```python
from idempy.middleware.flask import IdemMiddleware

app = Flask(__name__)
IdemMiddleware(app)                          # direct init
# or: middleware.init_app(app)               # application-factory pattern
```

Requires `pip install idempy[flask]`.

### FastAPI

```python
from idempy.middleware.fastapi import IdemMiddleware

app = FastAPI()
app.add_middleware(IdemMiddleware)
```

Requires `pip install idempy[fastapi]`.

### Django

```python
# settings.py
MIDDLEWARE = [
    "idempy.middleware.django.IdemMiddleware",
    ...
]
```

Optionally configure via `settings.IDEMPY`:

```python
IDEMPY = {
    "header_name": "Idempotency-Key",           # default
    "safe_methods": {"GET", "HEAD", "OPTIONS"},  # default
}
```

Requires `pip install idempy[django]`.

### Custom `Core` for all adapters

Pass a `core` argument to use a non-default store:

```python
from idempy import Core, RedisStore
from redis import Redis

core = Core(settings={"stores": {"redis": RedisStore(Redis.from_url(...))}, "default_store": "redis"})

# Flask
IdemMiddleware(app, core=core)

# FastAPI
app.add_middleware(IdemMiddleware, core=core)

# Django — set before the server starts
from idempy.middleware.django import IdemMiddleware as DjangoMiddleware
DjangoMiddleware.core = core
```

## Requirements

Python **3.11+**, no runtime dependencies for the core library.

Optional extras:

| Extra | Installs |
|---|---|
| `pip install idempy[redis]` | `redis` |
| `pip install idempy[flask]` | `flask` |
| `pip install idempy[fastapi]` | `fastapi`, `httpx` |
| `pip install idempy[django]` | `django` |
| `pip install idempy[all]` | all of the above |

## Installation

```bash
pip install idempy
```

For development:

```bash
pip install -e ".[dev]"
# or
uv sync --extra dev
```

## Development

```bash
pytest                              # all tests
pytest tests/integration/           # integration tests only
```

## Project structure

```
idempy/
├── core.py              Core orchestration (begin / complete / fail / replay / get_status)
├── base.py              BaseStore ABC — implement this for custom backends
├── memory.py            MemoryStore — thread-safe in-process backend
├── redis.py             RedisStore — distributed backend
├── stores.py            Stores registry
├── models.py            Dataclasses and enums (Request, IdempotencyRecord, Status, …)
├── errors.py            Exception hierarchy
├── validator.py         ValidatedField descriptor + built-in validators
├── logging.py           NullHandler registration + configure_logging() helper
└── middleware/
    ├── flask.py         Flask extension
    ├── fastapi.py       FastAPI / Starlette middleware
    └── django.py        Django middleware

tests/
├── integration/         End-to-end lifecycle tests (MemoryStore + RedisStore)
└── ...                  Unit tests per module
```

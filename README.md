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

`idempy` aims to solve that by tracking idempotency keys, request fingerprints, execution state, and stored results.

## Current goal

The current version is focused on a **pure Python core** first.

The aim is to build a small, clear library that can:

- store idempotency records
- detect duplicate requests
- reject conflicting reuse of a key
- track in-progress operations
- replay completed results safely

## Project structure

```text
idempy/
├── models.py
├── errors.py
├── base.py
├── core.py
└── memory.py
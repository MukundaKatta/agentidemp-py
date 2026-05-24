# agentidemp-py

[![PyPI](https://img.shields.io/pypi/v/agentidemp-py.svg)](https://pypi.org/project/agentidemp-py/)
[![Python](https://img.shields.io/pypi/pyversions/agentidemp-py.svg)](https://pypi.org/project/agentidemp-py/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**Idempotency keys for LLM agent retries.**

When an agent retries a request, on a 429, a timeout, or a cache miss-aware
policy, the retry needs the **same** idempotency key as the first attempt.
Otherwise the dedup layer treats it as a new request and you double-bill or
double-dispatch.

`agentidemp-py` derives stable keys from request content, so retries get the
same key automatically. Three forms: short sha256 hex, deterministic UUIDv5,
and a scoped helper for per-tenant dedup.

Sibling to the Rust crate
[`agentidemp-rs`](https://crates.io/crates/agentidemp-rs).
Pairs with [`cachebench`](https://github.com/MukundaKatta/cachebench) for
miss-aware retry that keeps the same key across attempts.

## Install

```bash
pip install agentidemp-py
```

Zero runtime deps. Stdlib `hashlib` + `uuid` only.

## Use

```python
from agentidemp import sha256_hex, uuid5_key, NAMESPACE_ANTHROPIC

body = b'{"model":"claude-sonnet-4-20250514","messages":[{"role":"user","content":"hi"}]}'

# Short hex form (35 chars: "ik_" + 32 hex):
key1 = sha256_hex(body)
# -> "ik_a3f9c1d8b2e7f046189f43a2b8e7c106"

# UUIDv5 form (36-char UUID string for `Idempotency-Key: <uuid>` headers):
key2 = uuid5_key(NAMESPACE_ANTHROPIC, body)
# -> "5fd2604e-..."

# Fresh random key when you don't have content to derive from:
from agentidemp import random_key
key3 = random_key()
```

### Scoped keys

If the same prompt body might recur across tenants or users and you want
per-scope dedup, prefix with a scope:

```python
from agentidemp import scoped_sha256_hex, scoped_key

# Single scope + content (matches the Rust sibling API):
k = scoped_sha256_hex("tenant-42", body)

# Variadic convenience: scope plus any number of parts:
k = scoped_key("tenant-42", "user-7", body)
```

The scope and each part are separated by a null byte so `"ab" + "c"` does
not collide with `"a" + "bc"`.

### Composing with cachebench

`cachebench`'s miss-aware policy retries on a silent cache miss. Pair with
`agentidemp` so the retry is recognized as the same request:

```python
from agentidemp import sha256_hex

key = sha256_hex(request_body_bytes)
headers = {"Idempotency-Key": key, ...}
# retries built by your cachebench policy reuse the same body, so the
# same key flows through and your dedup layer recognizes the retry.
```

## What it does NOT do

- No HTTP. Returns a string. You set the header.
- No response caching. That belongs to a different layer (see `cachebench`).
- No tracking of which keys you have already used. Stateless by design.

## License

MIT

"""agentidemp - idempotency keys for LLM agent retries.

When an agent retries a request (a 429, a timeout, or a cachebench
miss-aware retry) the retry needs the SAME idempotency key as the first
attempt. Otherwise the dedup layer treats it as a new request and you
double-bill or double-dispatch.

`agentidemp` derives stable keys from request content. Three flavors:

  * `sha256_hex(content)` - short `ik_` + 32-hex string. Good for the
    `Idempotency-Key` header on providers that don't require a UUID.
  * `uuid5_key(namespace, name)` - deterministic UUIDv5 string. Use when
    the destination expects a UUID-shaped idempotency key.
  * `scoped_sha256_hex(scope, content)` / `scoped_key(scope, *parts)` -
    per-tenant or per-user dedup when the same body might recur.

Plus `random_key()` for the fresh-key case (UUIDv4).

    from agentidemp import sha256_hex, uuid5_key, NAMESPACE_ANTHROPIC

    body = b'{"model":"claude","messages":[{"role":"user","content":"hi"}]}'
    key  = sha256_hex(body)
    # -> "ik_a3f9c1d8b2e7f046189f43a2b8e7c106"

    uuid = uuid5_key(NAMESPACE_ANTHROPIC, body)
    # -> "5fd2604e-..."

Sibling to the Rust crate `agentidemp-rs`. Pairs with `cachebench` for
miss-aware retry that keeps the same key across attempts.
"""

from agentidemp.keys import (
    NAMESPACE_ANTHROPIC,
    NAMESPACE_DNS,
    random,
    random_key,
    scoped_key,
    scoped_sha256_hex,
    sha256_hex,
    uuid5_key,
    uuid_v5,
)

__version__ = "0.1.0"

__all__ = [
    "NAMESPACE_ANTHROPIC",
    "NAMESPACE_DNS",
    "__version__",
    "random",
    "random_key",
    "scoped_key",
    "scoped_sha256_hex",
    "sha256_hex",
    "uuid5_key",
    "uuid_v5",
]

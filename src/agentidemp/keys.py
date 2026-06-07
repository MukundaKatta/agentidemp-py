"""Idempotency key helpers."""

from __future__ import annotations

import hashlib
import uuid

# ---- public namespace constants ----

# Standard RFC 4122 DNS namespace, re-exported as a convenient anchor for
# users who don't want to define their own. This matches the Rust sibling's
# `NAMESPACE_ANTHROPIC` constant byte-for-byte. The name is historical.
NAMESPACE_ANTHROPIC: uuid.UUID = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")

# Alias under a generic name for callers that prefer it.
NAMESPACE_DNS: uuid.UUID = NAMESPACE_ANTHROPIC

# Idempotency-key prefix; mirrors the Rust crate's `ik_` marker.
_PREFIX = "ik_"

# Number of leading sha256 digest bytes used for the hex portion.
_HEX_BYTES = 16
# Length of the hex portion (16 bytes = 32 hex chars).
_HEX_LEN = _HEX_BYTES * 2


def _coerce_bytes(content: str | bytes, *, name: str = "content") -> bytes:
    """Accept `str` (utf-8 encoded) or `bytes`. Anything else is a TypeError."""
    if isinstance(content, bytes):
        return content
    if isinstance(content, str):
        return content.encode("utf-8")
    raise TypeError(f"{name} must be str or bytes, got {type(content).__name__}")


def sha256_hex(content: str | bytes) -> str:
    """Compute a 16-byte sha256 prefix of `content`, hex-encoded, with the
    `ik_` marker prefix.

    Returns a 35-character string (3 prefix + 32 hex).

    Same content always produces the same key. Useful for the
    `Idempotency-Key` HTTP header on providers that don't require a UUID.
    """
    data = _coerce_bytes(content)
    digest = hashlib.sha256(data).digest()
    return _PREFIX + digest[:_HEX_BYTES].hex()


def uuid5_key(namespace: uuid.UUID, name: str | bytes) -> str:
    """Compute a deterministic UUID v5 string for `name` under `namespace`.

    Same namespace + same name always produces the same UUID. Use this when
    the destination expects a UUID-shaped idempotency key.

    Returns the standard 36-character UUID string (8-4-4-4-12 hex with hyphens).
    """
    if not isinstance(namespace, uuid.UUID):
        raise TypeError(f"namespace must be uuid.UUID, got {type(namespace).__name__}")
    # uuid.uuid5 expects a str; if bytes were passed, decode as utf-8 to
    # match the Rust crate's `&[u8]` behavior.
    if isinstance(name, bytes):
        name_str = name.decode("utf-8")
    elif isinstance(name, str):
        name_str = name
    else:
        raise TypeError(f"name must be str or bytes, got {type(name).__name__}")
    return str(uuid.uuid5(namespace, name_str))


# Convenience alias mirroring the Rust crate's `uuid_v5` name.
uuid_v5 = uuid5_key


def random_key() -> str:
    """Generate a fresh random UUID v4 string.

    For the case where you don't have content to derive from (e.g. the very
    first attempt with no prior key to reuse)."""
    return str(uuid.uuid4())


# Alias mirroring the Rust crate's bare `random` name.
random = random_key


def scoped_sha256_hex(scope: str, content: str | bytes) -> str:
    """Combine `scope` and `content` into a single hashed key. Useful when
    the same content might recur across users or tenants and you want
    per-scope deduplication.

    The scope and content are separated by a null byte so `"ab" + "c"`
    doesn't collide with `"a" + "bc"`.

    Returns a 35-character string in the same `ik_` + 32-hex shape as
    `sha256_hex`.
    """
    if not isinstance(scope, str):
        raise TypeError(f"scope must be str, got {type(scope).__name__}")
    data = _coerce_bytes(content)
    hasher = hashlib.sha256()
    hasher.update(scope.encode("utf-8"))
    hasher.update(b"\x00")
    hasher.update(data)
    return _PREFIX + hasher.digest()[:_HEX_BYTES].hex()


def scoped_key(scope: str, *parts: str | bytes) -> str:
    """Join `scope` and any number of `parts` into one stable key.

    Variadic convenience form for callers that want to dedupe across a
    composite identity (e.g. tenant + user + body). Each segment is
    separated by a null byte so adjacent parts can't collide by
    concatenation.

    Returns a 35-character string in the same `ik_` + 32-hex shape as
    `sha256_hex`.
    """
    if not isinstance(scope, str):
        raise TypeError(f"scope must be str, got {type(scope).__name__}")
    hasher = hashlib.sha256()
    hasher.update(scope.encode("utf-8"))
    for i, part in enumerate(parts):
        hasher.update(b"\x00")
        hasher.update(_coerce_bytes(part, name=f"parts[{i}]"))
    return _PREFIX + hasher.digest()[:_HEX_BYTES].hex()

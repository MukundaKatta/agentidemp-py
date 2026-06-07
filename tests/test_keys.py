import hashlib
import uuid

import pytest

from agentidemp import (
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

# ---------- sha256_hex ----------


def test_sha256_hex_shape():
    k = sha256_hex(b"hello")
    assert k.startswith("ik_")
    assert len(k) == 3 + 32
    # everything after the prefix must be lowercase hex
    int(k[3:], 16)


def test_sha256_hex_stable_for_same_input():
    a = sha256_hex(b"some-prompt-body")
    b = sha256_hex(b"some-prompt-body")
    assert a == b


def test_sha256_hex_different_for_different_input():
    a = sha256_hex(b"prompt A")
    b = sha256_hex(b"prompt B")
    assert a != b


def test_sha256_hex_str_and_bytes_match():
    # passing the same content as str or bytes gives the same key
    assert sha256_hex("hello") == sha256_hex(b"hello")


def test_sha256_hex_str_is_utf8_encoded():
    s = "héllo"  # contains a multi-byte char
    assert sha256_hex(s) == sha256_hex(s.encode("utf-8"))


def test_sha256_hex_empty_input_is_stable():
    a = sha256_hex(b"")
    b = sha256_hex("")
    assert a == b
    assert a.startswith("ik_")
    assert len(a) == 35


def test_sha256_hex_matches_first_16_bytes_of_sha256():
    content = b"the quick brown fox"
    expected = "ik_" + hashlib.sha256(content).digest()[:16].hex()
    assert sha256_hex(content) == expected


def test_sha256_hex_type_error():
    with pytest.raises(TypeError):
        sha256_hex(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        sha256_hex(None)  # type: ignore[arg-type]


# ---------- uuid5_key ----------


def test_uuid5_key_is_deterministic():
    a = uuid5_key(NAMESPACE_ANTHROPIC, "request-1")
    b = uuid5_key(NAMESPACE_ANTHROPIC, "request-1")
    assert a == b


def test_uuid5_key_different_names_differ():
    a = uuid5_key(NAMESPACE_ANTHROPIC, "request-1")
    b = uuid5_key(NAMESPACE_ANTHROPIC, "request-2")
    assert a != b


def test_uuid5_key_different_namespaces_differ():
    other = uuid.UUID("00000000-0000-0000-0000-000000000001")
    a = uuid5_key(NAMESPACE_ANTHROPIC, "same-name")
    b = uuid5_key(other, "same-name")
    assert a != b


def test_uuid5_key_returns_uuid_string_shape():
    s = uuid5_key(NAMESPACE_ANTHROPIC, "x")
    # round-trip parses cleanly as a UUID
    parsed = uuid.UUID(s)
    assert parsed.version == 5
    assert len(s) == 36
    assert s.count("-") == 4


def test_uuid5_key_accepts_bytes_name():
    a = uuid5_key(NAMESPACE_ANTHROPIC, b"hello")
    b = uuid5_key(NAMESPACE_ANTHROPIC, "hello")
    assert a == b


def test_uuid5_key_namespace_type_error():
    with pytest.raises(TypeError):
        uuid5_key("not-a-uuid", "name")  # type: ignore[arg-type]


def test_uuid5_key_name_type_error():
    with pytest.raises(TypeError):
        uuid5_key(NAMESPACE_ANTHROPIC, 42)  # type: ignore[arg-type]


def test_uuid_v5_alias_matches_uuid5_key():
    assert uuid_v5(NAMESPACE_ANTHROPIC, "foo") == uuid5_key(NAMESPACE_ANTHROPIC, "foo")


# ---------- scoped_sha256_hex (Rust API parity) ----------


def test_scoped_sha256_hex_shape():
    k = scoped_sha256_hex("tenant-42", b"body")
    assert k.startswith("ik_")
    assert len(k) == 35


def test_scoped_sha256_hex_different_scopes_differ():
    a = scoped_sha256_hex("tenant-A", b"body")
    b = scoped_sha256_hex("tenant-B", b"body")
    assert a != b


def test_scoped_sha256_hex_separator_avoids_collision():
    # null-byte separator means "ab"+"c" must not equal "a"+"bc"
    a = scoped_sha256_hex("ab", b"c")
    b = scoped_sha256_hex("a", b"bc")
    assert a != b


def test_scoped_sha256_hex_str_and_bytes_content_match():
    assert scoped_sha256_hex("scope", "data") == scoped_sha256_hex("scope", b"data")


def test_scoped_sha256_hex_differs_from_plain_sha256_hex():
    # same body with any scope should differ from the unscoped key
    plain = sha256_hex(b"body")
    scoped = scoped_sha256_hex("", b"body")
    assert plain != scoped  # null-byte separator alone changes the digest


def test_scoped_sha256_hex_scope_type_error():
    with pytest.raises(TypeError):
        scoped_sha256_hex(123, b"body")  # type: ignore[arg-type]


def test_scoped_sha256_hex_content_type_error():
    with pytest.raises(TypeError):
        scoped_sha256_hex("scope", 123)  # type: ignore[arg-type]


# ---------- scoped_key (variadic convenience) ----------


def test_scoped_key_basic_two_parts_matches_scoped_sha256_hex():
    # one part should be equivalent to scoped_sha256_hex
    a = scoped_key("tenant-42", b"body")
    b = scoped_sha256_hex("tenant-42", b"body")
    assert a == b


def test_scoped_key_with_multiple_parts():
    a = scoped_key("tenant-42", "user-7", b"body")
    b = scoped_key("tenant-42", "user-7", b"body")
    assert a == b
    assert a.startswith("ik_")
    assert len(a) == 35


def test_scoped_key_part_order_matters():
    a = scoped_key("tenant", "user-1", "user-2")
    b = scoped_key("tenant", "user-2", "user-1")
    assert a != b


def test_scoped_key_extra_part_changes_output():
    a = scoped_key("tenant", "body")
    b = scoped_key("tenant", "body", "extra")
    assert a != b


def test_scoped_key_empty_parts_still_separated():
    # adding an empty extra part still affects the digest (separator is hashed)
    a = scoped_key("scope", "x")
    b = scoped_key("scope", "x", "")
    assert a != b


def test_scoped_key_with_no_parts_uses_scope_only():
    a = scoped_key("just-scope")
    assert a.startswith("ik_")
    assert len(a) == 35


def test_scoped_key_part_type_error():
    with pytest.raises(TypeError):
        scoped_key("scope", 123)  # type: ignore[arg-type]


# ---------- random_key ----------


def test_random_key_shape():
    s = random_key()
    parsed = uuid.UUID(s)
    assert parsed.version == 4
    assert len(s) == 36


def test_random_key_is_not_deterministic():
    a = random_key()
    b = random_key()
    assert a != b


def test_random_alias_is_random_key():
    # the bare `random` export mirrors the Rust crate's name and must be the
    # same callable as random_key
    assert random is random_key


# ---------- namespace constants ----------


def test_namespace_aliases_are_equal():
    assert NAMESPACE_ANTHROPIC == NAMESPACE_DNS


def test_namespace_matches_rust_constant():
    # bytes match the Rust source's NAMESPACE_ANTHROPIC byte array
    expected = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
    assert expected == NAMESPACE_ANTHROPIC

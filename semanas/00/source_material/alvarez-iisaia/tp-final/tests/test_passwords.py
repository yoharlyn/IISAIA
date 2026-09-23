from backend.services.auth import hash_password, verify_password


def test_argon2_hash_is_salted_and_verifiable() -> None:
    first = hash_password("UnaClaveSegura123!")
    second = hash_password("UnaClaveSegura123!")
    assert first != second
    assert first.startswith("$argon2id$")
    assert verify_password(first, "UnaClaveSegura123!")
    assert not verify_password(first, "incorrecta")

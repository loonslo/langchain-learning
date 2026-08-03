import pytest
from customer_support.auth import AuthenticationError, Identity, TokenVerifier


def test_signed_identity_works_and_tampering_fails():
    verifier = TokenVerifier("day63-test-secret-at-least-32-bytes")
    token = verifier.issue(Identity("shop", "alice"))
    assert verifier.verify("Bearer " + token).user_id == "alice"
    with pytest.raises(AuthenticationError):
        verifier.verify("Bearer " + token[:-2] + "xx")

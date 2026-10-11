import pytest

from app.models.schemas import CanonicalIntent, State
from app.security.intent_lock import TRANSITIONS, sign, transition, verify


def canonical():
    return CanonicalIntent(
        intent_id="i",
        user_id="alice",
        source_account_id="a",
        beneficiary_id="b",
        amount_minor=10000,
        currency="INR",
        operation="TRANSFER",
        expires_at=2000000000,
        nonce="n",
        policy_version="1.0",
    )


def test_determinism():
    c = canonical()
    assert sign(c, "secret") == sign(c, "secret")
    assert verify(c, sign(c, "secret"), "secret")


@pytest.mark.parametrize(
    "field,value",
    [
        ("amount_minor", 100000),
        ("beneficiary_id", "other"),
        ("source_account_id", "other"),
        ("currency", "USD"),
        ("expires_at", 1),
        ("nonce", "new"),
    ],
)
def test_tamper(field, value):
    c = canonical()
    assert not verify(c.model_copy(update={field: value}), sign(c, "secret"), "secret")


@pytest.mark.parametrize("before", list(State))
@pytest.mark.parametrize("after", list(State))
def test_transition_table(before, after):
    if after in TRANSITIONS[before]:
        assert transition(before, after) == after
    else:
        with pytest.raises(ValueError):
            transition(before, after)

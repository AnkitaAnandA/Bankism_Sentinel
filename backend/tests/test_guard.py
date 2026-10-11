import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.banking.intent_parser import parse
from app.banking.transfer_service import TransferService
from app.config import Settings
from app.data.seed import seed
from app.models.database import Account, Beneficiary, Database, Intent, Transaction
from app.models.schemas import CanonicalIntent, DomainError, State
from app.security.intent_lock import canonical_bytes, sign


@pytest.fixture
def bank(tmp_path):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path}/test.db",
        intent_hmac_key="a" * 64,
        session_signing_key="b" * 64,
    )
    db = Database(settings.database_url)
    seed(db)
    yield db, TransferService(db, settings)
    db.engine.dispose()


def prepared(service):
    return service.prepare("alice", parse("Transfer ₹1,000 to Rahul"))


def confirmed(service):
    ident, v = prepared(service)
    service.confirm("alice", ident, v.integrity_tag, "confirm")
    return ident


def balances(db):
    with db.sessions() as s:
        return (
            s.get(Account, "alice-checking").balance_minor,
            s.get(Account, "rahul-checking").balance_minor,
        )


def test_seed_idempotent(bank):
    db, _ = bank
    before = balances(db)
    seed(db)
    assert balances(db) == before


def test_concurrent_exactly_once(bank):
    db, service = bank
    ident = confirmed(service)
    before = balances(db)

    def run(_):
        try:
            service.execution_guard("alice", ident, uuid.uuid4().hex)
            return True
        except DomainError:
            return False

    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(run, range(16))) == 1
    after = balances(db)
    assert after == (before[0] - 100000, before[1] + 100000)
    with db.sessions() as s:
        assert len(s.query(Transaction).all()) == 1


def test_atomic_failure(bank):
    db, service = bank
    ident = confirmed(service)
    before = balances(db)

    def fault():
        raise RuntimeError("injected crash")

    with pytest.raises(RuntimeError):
        service.execution_guard("alice", ident, uuid.uuid4().hex, fault=fault)
    assert balances(db) == before
    with db.sessions() as s:
        assert s.get(Intent, ident).status == State.CONFIRMED
        assert not s.query(Transaction).all()


@pytest.mark.parametrize(
    "failure",
    [
        "identity",
        "unconfirmed",
        "tag",
        "expired",
        "fields",
        "policy",
        "idempotency",
        "classifier",
    ],
)
def test_guard_failures_no_debit(bank, failure):
    db, service = bank
    ident, v = prepared(service)
    if failure != "unconfirmed":
        service.confirm("alice", ident, v.integrity_tag, "confirm")
    key = uuid.uuid4().hex
    with db.write() as s:
        row = s.get(Intent, ident)
        if failure == "tag":
            row.integrity_tag = "0" * 64
        elif failure == "expired":
            c = CanonicalIntent.model_validate_json(row.canonical_payload).model_copy(
                update={"expires_at": int(time.time()) - 1}
            )
            row.expires_at, row.canonical_payload, row.integrity_tag = (
                c.expires_at,
                canonical_bytes(c).decode(),
                sign(c, service.settings.intent_hmac_key),
            )
        elif failure == "fields":
            row.amount_minor = 1000000
        elif failure == "policy":
            s.get(Beneficiary, row.beneficiary_id).approved = False
    if failure == "idempotency":
        other = confirmed(service)
        service.execution_guard("alice", other, key)
    before = balances(db)
    with pytest.raises(DomainError):
        service.execution_guard(
            "rahul" if failure == "identity" else "alice",
            ident,
            key,
            classifier_healthy=failure != "classifier",
        )
    assert balances(db) == before


def test_correction_and_confirmed_immutability(bank):
    db, service = bank
    first, old = prepared(service)
    second, corrected = service.prepare("alice", parse("Use my savings account"), first)
    assert old.integrity_tag != corrected.integrity_tag
    assert corrected.amount_minor == old.amount_minor
    assert corrected.source_account == "savings"
    with pytest.raises(DomainError):
        service.confirm("alice", first, old.integrity_tag, "confirm")
    service.confirm("alice", second, corrected.integrity_tag, "confirm")
    with pytest.raises(DomainError):
        service.prepare("alice", parse("make it ₹600"), second)


def test_replay_confirmation(bank):
    db, service = bank
    ident, v = prepared(service)
    service.confirm("alice", ident, v.integrity_tag, "confirm")
    service.execution_guard("alice", ident, uuid.uuid4().hex)
    before = balances(db)
    with pytest.raises(DomainError):
        service.confirm("alice", ident, v.integrity_tag, "confirm")
    assert balances(db) == before


def test_correction_preserves_account_and_rejects_unknown_payee(bank):
    db, service = bank
    ident, v = service.prepare("alice", parse("Transfer ₹500 to Rahul from savings"))
    ident, v = service.prepare("alice", parse("make it ₹600"), ident)
    assert v.source_account == "savings"
    assert v.amount_minor == 60000
    with pytest.raises(DomainError):
        service.prepare("alice", parse("Transfer ₹600 to Unknown"), ident)
    with db.sessions() as s:
        assert s.get(Intent, ident).status == State.PENDING_CONFIRMATION

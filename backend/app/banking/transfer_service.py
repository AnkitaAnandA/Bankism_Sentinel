import hmac
import time
import uuid
from collections.abc import Callable

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.banking.mock_bank import transfer
from app.config import Settings
from app.models.database import Account, Beneficiary, Database, Intent, Transaction
from app.models.schemas import (
    CanonicalIntent,
    Category,
    DomainError,
    ParsedIntent,
    State,
    TransactionView,
)
from app.security.intent_lock import canonical_bytes, sign, transition, verify
from app.security.policy_engine import check_policy


def stored_canonical(row: Intent) -> CanonicalIntent:
    try:
        return CanonicalIntent.model_validate_json(row.canonical_payload)
    except ValueError as exc:
        raise DomainError(
            "Stored intent integrity failed", Category.PARAMETER_TAMPERING
        ) from exc


def match_fields(row: Intent, c: CanonicalIntent) -> None:
    if (
        (
            row.id,
            row.user_id,
            row.source_account_id,
            row.beneficiary_id,
            row.amount_minor,
            row.currency,
            row.expires_at,
        )
        != (
            c.intent_id,
            c.user_id,
            c.source_account_id,
            c.beneficiary_id,
            c.amount_minor,
            c.currency,
            c.expires_at,
        )
        or c.operation != "TRANSFER"
        or c.policy_version != "1.0"
    ):
        raise DomainError(
            "Stored transaction fields do not match the commitment",
            Category.PARAMETER_TAMPERING,
        )


def view(s: Session, row: Intent, transaction_id: str | None = None) -> TransactionView:
    payee = s.get(Beneficiary, row.beneficiary_id)
    source = s.get(Account, row.source_account_id)
    if not payee or not source:
        raise DomainError("Transaction references unavailable")
    return TransactionView(
        amount_minor=row.amount_minor,
        currency=row.currency,
        beneficiary_name=payee.beneficiary_name,
        masked_account="•••• " + payee.account_reference[-4:],
        source_account=source.name,
        expires_at=row.expires_at,
        integrity_tag=row.integrity_tag,
        status=State(row.status),
        transaction_id=transaction_id,
    )


class TransferService:
    def __init__(self, db: Database, settings: Settings):
        self.db, self.settings = db, settings

    def load_owned(self, s: Session, intent_id: str, user_id: str) -> Intent:
        row = s.scalar(select(Intent).where(Intent.id == intent_id).with_for_update())
        if not row or row.user_id != user_id:
            raise DomainError("Intent unavailable for this session", status=403)
        return row

    def prepare(
        self, user_id: str, parsed: ParsedIntent, old_id: str | None = None
    ) -> tuple[str, TransactionView]:
        with self.db.write() as s:
            old = self.load_owned(s, old_id, user_id) if old_id else None
            if old and old.status != State.PENDING_CONFIRMATION:
                raise DomainError(
                    "Only a pending proposal can be corrected",
                    Category.CROSS_TURN_MANIPULATION,
                )
            source = s.scalar(
                select(Account).where(
                    Account.user_id == user_id, Account.name == parsed.source
                )
            )
            payee = s.scalar(
                select(Beneficiary).where(
                    Beneficiary.user_id == user_id,
                    Beneficiary.beneficiary_name.ilike(parsed.beneficiary or ""),
                )
            )
            amount = parsed.amount_minor
            if old:
                c = stored_canonical(old)
                if not verify(c, old.integrity_tag, self.settings.intent_hmac_key):
                    raise DomainError(
                        "Old proposal integrity failed", Category.PARAMETER_TAMPERING
                    )
                match_fields(old, c)
                if old.expires_at <= int(time.time()):
                    raise DomainError("Proposal expired")
                amount = amount if amount is not None else old.amount_minor
                if parsed.beneficiary is None:
                    payee = s.get(Beneficiary, old.beneficiary_id)
                if not parsed.source_explicit:
                    source = s.get(Account, old.source_account_id)
            if not source:
                raise DomainError("Source account is not authorized", status=403)
            if not payee:
                raise DomainError(
                    "Beneficiary must be registered", Category.UNKNOWN_BENEFICIARY
                )
            if amount is None or parsed.ambiguous:
                raise DomainError(
                    "Please specify one exact transfer amount and recipient",
                    Category.AMBIGUOUS_INTENT,
                )
            check_policy(
                s,
                self.settings,
                user_id,
                source.id,
                payee.id,
                amount,
                parsed.currency,
                lock=True,
            )
            if old:
                old.status = transition(State(old.status), State.CANCELLED)
            ident = str(uuid.uuid4())
            canonical = CanonicalIntent(
                intent_id=ident,
                user_id=user_id,
                source_account_id=source.id,
                beneficiary_id=payee.id,
                amount_minor=amount,
                currency=parsed.currency,
                operation="TRANSFER",
                expires_at=int(time.time()) + self.settings.intent_ttl,
                nonce=uuid.uuid4().hex,
                policy_version="1.0",
            )
            row = Intent(
                id=ident,
                user_id=user_id,
                source_account_id=source.id,
                beneficiary_id=payee.id,
                amount_minor=amount,
                currency=parsed.currency,
                canonical_payload=canonical_bytes(canonical).decode(),
                integrity_tag=sign(canonical, self.settings.intent_hmac_key),
                status=State.DRAFT,
                expires_at=canonical.expires_at,
                classifier_safe=True,
            )
            row.status = transition(State(row.status), State.VALIDATED)
            row.status = transition(State(row.status), State.PENDING_CONFIRMATION)
            s.add(row)
            s.flush()
            return ident, view(s, row)

    def confirm(
        self, user_id: str, intent_id: str, tag: str, action: str
    ) -> TransactionView:
        with self.db.write() as s:
            row = self.load_owned(s, intent_id, user_id)
            c = stored_canonical(row)
            if not hmac.compare_digest(row.integrity_tag, tag) or not verify(
                c, row.integrity_tag, self.settings.intent_hmac_key
            ):
                raise DomainError(
                    "Intent integrity check failed", Category.PARAMETER_TAMPERING
                )
            match_fields(row, c)
            if row.status != State.PENDING_CONFIRMATION:
                raise DomainError(
                    "This proposal cannot be confirmed again", Category.REPLAY
                )
            if row.expires_at <= int(time.time()):
                raise DomainError("Proposal has expired")
            check_policy(
                s,
                self.settings,
                user_id,
                row.source_account_id,
                row.beneficiary_id,
                row.amount_minor,
                row.currency,
                lock=True,
            )
            row.status = transition(
                State(row.status),
                State.CONFIRMED if action == "confirm" else State.CANCELLED,
            )
            return view(s, row)

    def execution_guard(
        self,
        user_id: str,
        intent_id: str,
        key: str,
        classifier_healthy: bool = True,
        fault: Callable[[], None] | None = None,
    ) -> TransactionView:
        with self.db.write() as s:
            row = self.load_owned(s, intent_id, user_id)
            # Authorization is first; request and classifier supply no ledger arguments.
            source = s.get(Account, row.source_account_id)
            if not source or source.user_id != user_id:
                raise DomainError("Source account is not authorized", status=403)
            if row.status != State.CONFIRMED:
                raise DomainError(
                    "Exact intent must be explicitly confirmed and unused",
                    Category.REPLAY,
                )
            c = stored_canonical(row)
            if not verify(c, row.integrity_tag, self.settings.intent_hmac_key):
                raise DomainError(
                    "Intent integrity check failed", Category.PARAMETER_TAMPERING
                )
            if c.expires_at <= int(time.time()) or s.scalar(
                select(Transaction).where(Transaction.intent_id == intent_id)
            ):
                raise DomainError("Intent expired or already consumed", Category.REPLAY)
            match_fields(row, c)
            source, payee, destination = check_policy(
                s,
                self.settings,
                user_id,
                c.source_account_id,
                c.beneficiary_id,
                c.amount_minor,
                c.currency,
                lock=True,
            )
            if not row.classifier_safe or not classifier_healthy:
                raise DomainError(
                    "Configured classifier is unavailable; execution suspended",
                    Category.CLASSIFIER_UNAVAILABLE,
                )
            if s.scalar(select(Transaction).where(Transaction.idempotency_key == key)):
                raise DomainError(
                    "Idempotency key has already been used", Category.REPLAY
                )
            updated = s.execute(
                update(Intent)
                .where(Intent.id == row.id, Intent.status == State.CONFIRMED)
                .values(status=State.EXECUTED)
            )
            if updated.rowcount != 1:
                raise DomainError("Intent was consumed concurrently", Category.REPLAY)
            transfer(s, source, destination, c.amount_minor, fault)
            txid = str(uuid.uuid4())
            s.add(
                Transaction(
                    id=txid,
                    intent_id=row.id,
                    amount_minor=c.amount_minor,
                    source_account_id=source.id,
                    beneficiary_id=payee.id,
                    status="EXECUTED",
                    idempotency_key=key,
                    timestamp=int(time.time()),
                )
            )
            s.flush()
            row.status = State.EXECUTED
            return view(s, row, txid)

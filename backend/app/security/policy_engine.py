import time

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models.database import Account, Beneficiary, Transaction, User
from app.models.schemas import Category, DomainError


def check_policy(
    s: Session,
    settings: Settings,
    user_id: str,
    source_id: str,
    beneficiary_id: str,
    amount: int,
    currency: str,
    lock: bool = False,
) -> tuple[Account, Beneficiary, Account]:
    user_query = select(User).where(User.id == user_id)
    if lock:
        user_query = user_query.with_for_update()
    user = s.scalar(user_query)
    query = select(Account).where(Account.id == source_id)
    if lock:
        query = query.with_for_update()
    source = s.scalar(query)
    if not source or source.user_id != user_id or not user or user.role != "customer":
        raise DomainError("Source account is not authorized", status=403)
    payee = s.get(Beneficiary, beneficiary_id)
    if not payee or payee.user_id != user_id:
        raise DomainError(
            "Beneficiary must be registered", Category.UNKNOWN_BENEFICIARY
        )
    if not payee.approved:
        raise DomainError("Beneficiary is not approved")
    destination = s.get(Account, payee.account_reference)
    if (
        not destination
        or source.currency != currency
        or destination.currency != currency
    ):
        raise DomainError("Currency mismatch")
    if amount <= 0:
        raise DomainError("Amount must be positive")
    if amount > settings.per_transaction_limit:
        raise DomainError("Per-transaction limit exceeded")
    if source.balance_minor < amount:
        raise DomainError("Insufficient funds")
    day_start = int(time.time()) // 86400 * 86400
    spent = (
        s.scalar(
            select(func.coalesce(func.sum(Transaction.amount_minor), 0))
            .join(Account, Transaction.source_account_id == Account.id)
            .where(Account.user_id == user_id, Transaction.timestamp >= day_start)
        )
        or 0
    )
    if spent + amount > settings.daily_limit:
        raise DomainError("Daily transfer limit exceeded")
    return source, payee, destination

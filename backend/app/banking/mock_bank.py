from collections.abc import Callable

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.database import Account
from app.models.schemas import DomainError


def transfer(
    s: Session,
    source: Account,
    destination: Account,
    amount_minor: int,
    fault: Callable[[], None] | None = None,
) -> None:
    result = s.execute(
        update(Account)
        .where(Account.id == source.id, Account.balance_minor >= amount_minor)
        .values(balance_minor=Account.balance_minor - amount_minor)
    )
    if result.rowcount != 1:
        raise DomainError("Insufficient balance")
    if fault:
        fault()
    s.execute(
        update(Account)
        .where(Account.id == destination.id)
        .values(balance_minor=Account.balance_minor + amount_minor)
    )

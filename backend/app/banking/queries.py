from sqlalchemy import select

from app.models.database import Account, Beneficiary, Database, Transaction
from app.models.schemas import AccountView, HistoryView


def accounts_and_history(
    db: Database, user_id: str
) -> tuple[list[AccountView], list[HistoryView]]:
    with db.sessions() as s:
        accounts = s.scalars(select(Account).where(Account.user_id == user_id)).all()
        history = s.execute(
            select(Transaction, Beneficiary)
            .join(Beneficiary, Transaction.beneficiary_id == Beneficiary.id)
            .join(Account, Transaction.source_account_id == Account.id)
            .where(Account.user_id == user_id)
            .order_by(Transaction.timestamp.desc())
            .limit(5)
        ).all()
        return (
            [
                AccountView(
                    id=a.id,
                    name=a.name,
                    masked_account="•••• " + a.id[-4:],
                    balance_minor=a.balance_minor,
                    currency=a.currency,
                )
                for a in accounts
            ],
            [
                HistoryView(
                    id=t.id,
                    amount_minor=t.amount_minor,
                    currency="INR",
                    beneficiary_name=b.beneficiary_name,
                    timestamp=t.timestamp,
                )
                for t, b in history
            ],
        )

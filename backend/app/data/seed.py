from app.models.database import Account, Beneficiary, Database, User


def seed(db: Database) -> None:
    db.create()
    with db.write() as s:
        if s.get(User, "alice"):
            return
        s.add_all(
            [
                User(id="alice", display_name="Aditi Sharma", role="customer"),
                User(id="rahul", display_name="Rahul Mehta", role="customer"),
                User(id="analyst", display_name="Security Analyst", role="analyst"),
            ]
        )
        s.flush()
        s.add_all(
            [
                Account(
                    id="alice-checking",
                    user_id="alice",
                    name="checking",
                    currency="INR",
                    balance_minor=25000000,
                ),
                Account(
                    id="alice-savings",
                    user_id="alice",
                    name="savings",
                    currency="INR",
                    balance_minor=50000000,
                ),
                Account(
                    id="rahul-checking",
                    user_id="rahul",
                    name="checking",
                    currency="INR",
                    balance_minor=10000000,
                ),
            ]
        )
        s.flush()
        s.add_all(
            [
                Beneficiary(
                    id="payee-rahul",
                    user_id="alice",
                    beneficiary_name="Rahul",
                    account_reference="rahul-checking",
                    approved=True,
                ),
                Beneficiary(
                    id="payee-unapproved",
                    user_id="alice",
                    beneficiary_name="Neha",
                    account_reference="rahul-checking",
                    approved=False,
                ),
                Beneficiary(
                    id="payee-aditi",
                    user_id="rahul",
                    beneficiary_name="Aditi",
                    account_reference="alice-checking",
                    approved=True,
                ),
            ]
        )

import pytest

from app.banking.intent_parser import parse
from app.models.database import Account
from app.models.schemas import DomainError


@pytest.mark.parametrize(
    "message",
    [
        "Transfer ₹0 to Rahul",
        "Transfer ₹8,00,000 to Rahul",
        "Transfer ₹500 to Neha",
        "Transfer ₹500 to Unknown",
        "Transfer ₹500 USD to Rahul",
    ],
)
def test_policy_blocks(bank, message):
    _, service = bank
    with pytest.raises(DomainError):
        service.prepare("alice", parse(message))


def test_balance_and_daily(bank):
    db, service = bank
    with db.write() as s:
        s.get(Account, "alice-checking").balance_minor = 1
    with pytest.raises(DomainError):
        service.prepare("alice", parse("Transfer ₹500 to Rahul"))
    service.settings.daily_limit = 1
    with pytest.raises(DomainError):
        service.prepare("alice", parse("Transfer ₹500 to Rahul from savings"))

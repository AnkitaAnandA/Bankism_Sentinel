import re
from decimal import Decimal, InvalidOperation

from app.models.schemas import Operation, ParsedIntent
from app.security.rule_detector import informational

TRANSFER = re.compile(r"\b(?:transfer|send|pay|move|make it|use my)\b", re.I)
AMOUNT = re.compile(
    r"(?:₹|\bINR\s*|\brupees?\s*)\s*([+-]?\d[\d,]*(?:\.\d{1,2})?)(?![\d.])|\b([+-]?\d[\d,]*(?:\.\d{1,2})?)\s*(?:rupees?|INR)\b",
    re.I,
)
BARE_AMOUNT = re.compile(
    r"\b(?:transfer|send|pay|make it)\s+([+-]?\d[\d,]*(?:\.\d{1,2})?)(?![\d.])", re.I
)
PAYEE = re.compile(
    r"\bto\s+(?:(?:my|a|the|registered|approved)\s+){0,3}(?:payee\s+|beneficiary\s+)?([a-zA-Z]+)",
    re.I,
)
MEMO = re.compile(r"\bmemo\s*:\s*(.*)", re.I | re.S)
MONEY_WORDS = re.compile(
    r"\b(five hundred|one thousand|two thousand|fifteen hundred|five thousand)\b", re.I
)
WORD_VALUES = {
    "five hundred": 50000,
    "one thousand": 100000,
    "two thousand": 200000,
    "fifteen hundred": 150000,
    "five thousand": 500000,
}
INVALID_NUMBER = re.compile(r"\d\.\d{3,}|\d[eE][+-]?\d")
COMPOUND = re.compile(r"\b(?:then|instead|or|change|another|also|and)\b", re.I)
GROUPING = re.compile(
    r"^[+-]?(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d{1,2})?$"
)


def parse(text: str) -> ParsedIntent:
    if informational(text):
        return ParsedIntent(operation=Operation.INFORMATIONAL)
    memo = MEMO.search(text)
    body = text[: memo.start()] if memo else text
    if TRANSFER.search(body):
        matches = list(AMOUNT.finditer(body)) or list(BARE_AMOUNT.finditer(body))
        amount = None
        if len(matches) == 1:
            raw = matches[0].group(1) or matches[0].group(2)
            try:
                value = Decimal(raw.replace(",", "")) * 100
                if value == value.to_integral_value() and GROUPING.fullmatch(raw):
                    amount = int(value)
            except InvalidOperation:
                pass
        words = MONEY_WORDS.search(body)
        if amount is None and words:
            amount = WORD_VALUES[words.group().lower()]
        payee = PAYEE.search(body)
        beneficiary = payee.group(1) if payee else None
        if beneficiary and beneficiary.lower() in {
            "payee",
            "beneficiary",
            "registered",
            "approved",
            "account",
        }:
            beneficiary = None
        return ParsedIntent(
            operation=Operation.TRANSFER,
            amount_minor=amount,
            beneficiary=beneficiary,
            source="savings" if "savings" in body.lower() else "checking",
            source_explicit="savings" in body.lower() or "checking" in body.lower(),
            currency="USD" if "$" in body or "USD" in body.upper() else "INR",
            memo=memo.group(1) if memo else "",
            ambiguous=bool(
                len(matches) > 1 or COMPOUND.search(body) or INVALID_NUMBER.search(body)
            ),
        )
    if "balance" in body.lower():
        return ParsedIntent(operation=Operation.BALANCE)
    if "transactions" in body.lower() or "history" in body.lower():
        return ParsedIntent(operation=Operation.HISTORY)
    return ParsedIntent(operation=Operation.UNKNOWN, ambiguous=True)

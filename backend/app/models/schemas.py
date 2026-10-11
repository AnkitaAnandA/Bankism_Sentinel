from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, StrictInt


class Verdict(StrEnum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    REVIEW = "REVIEW"


class Risk(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Category(StrEnum):
    NONE = "NONE"
    DIRECT_INJECTION = "DIRECT_INJECTION"
    POLICY_OVERRIDE = "POLICY_OVERRIDE"
    ROLE_SPOOFING = "ROLE_SPOOFING"
    ROLEPLAY_JAILBREAK = "ROLEPLAY_JAILBREAK"
    OBFUSCATION = "OBFUSCATION"
    ENCODED_PAYLOAD = "ENCODED_PAYLOAD"
    MEMO_INJECTION = "MEMO_INJECTION"
    DATA_EXFILTRATION = "DATA_EXFILTRATION"
    CROSS_TURN_MANIPULATION = "CROSS_TURN_MANIPULATION"
    REPLAY = "REPLAY"
    PARAMETER_TAMPERING = "PARAMETER_TAMPERING"
    UNKNOWN_BENEFICIARY = "UNKNOWN_BENEFICIARY"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    CLASSIFIER_UNAVAILABLE = "CLASSIFIER_UNAVAILABLE"
    AMBIGUOUS_INTENT = "AMBIGUOUS_INTENT"


class Operation(StrEnum):
    BALANCE = "BALANCE"
    HISTORY = "HISTORY"
    TRANSFER = "TRANSFER"
    INFORMATIONAL = "INFORMATIONAL"
    UNKNOWN = "UNKNOWN"


class State(StrEnum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    CONFIRMED = "CONFIRMED"
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Role(StrEnum):
    CUSTOMER = "customer"
    ANALYST = "analyst"


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Immutable(Model):
    model_config = ConfigDict(extra="forbid", frozen=True)


class CanonicalIntent(Immutable):
    intent_id: str
    user_id: str
    source_account_id: str
    beneficiary_id: str
    amount_minor: StrictInt
    currency: str
    operation: str
    expires_at: StrictInt
    nonce: str
    policy_version: str


class Finding(Immutable):
    category: Category
    risk: Risk
    evidence: str
    view: str


class Classification(Immutable):
    is_injection: bool = Field(strict=True)
    risk_level: Risk
    threat_category: Category
    evidence: str = Field(max_length=200)
    detected_intent: Operation


class ParsedIntent(Immutable):
    operation: Operation
    amount_minor: StrictInt | None = None
    beneficiary: str | None = None
    source: str = "checking"
    source_explicit: bool = False
    currency: str = "INR"
    memo: str = ""
    ambiguous: bool = False


class Context(Model):
    intent_id: str | None = Field(default=None, max_length=64)


class AnalyzeRequest(Model):
    message: str = Field(min_length=1, max_length=2000, strict=True)
    context: Context = Field(default_factory=Context)


class ConfirmRequest(Model):
    integrity_tag: str = Field(min_length=64, max_length=64, strict=True)
    action: str = Field(default="confirm", pattern="^(confirm|cancel)$")


class ExecuteRequest(Model):
    intent_id: str = Field(min_length=1, max_length=64, strict=True)
    idempotency_key: str = Field(min_length=8, max_length=128, strict=True)


class Checks(Model):
    injection_safe: bool = False
    account_authorized: bool = False
    transaction_valid: bool = False


class TransactionView(Model):
    amount_minor: StrictInt
    currency: str
    beneficiary_name: str
    masked_account: str
    source_account: str
    expires_at: StrictInt
    integrity_tag: str
    status: State
    transaction_id: str | None = None


class AccountView(Model):
    id: str
    name: str
    masked_account: str
    balance_minor: StrictInt
    currency: str


class HistoryView(Model):
    id: str
    amount_minor: StrictInt
    currency: str
    beneficiary_name: str
    timestamp: StrictInt


class EventView(Model):
    request_id: str
    category: Category
    risk: Risk
    verdict: Verdict
    evidence: str
    timestamp: StrictInt


class EvaluationRow(Model):
    configuration: str
    dataset_size: StrictInt
    recall: float
    false_positive_rate: float
    unauthorized_transfers: StrictInt
    schema_validity: float
    valid_transfer_completion: float
    duplicate_prevention: float
    tamper_rejection: float


class Metrics(Model):
    total: StrictInt
    allow: StrictInt
    block: StrictInt
    review: StrictInt
    categories: dict[str, int]


class Response(Model):
    request_id: str
    verdict: Verdict = Verdict.BLOCK
    approved: bool = False
    risk_level: Risk = Risk.HIGH
    threat_category: Category = Category.POLICY_VIOLATION
    detected_intent: Operation = Operation.UNKNOWN
    reason: str
    policy_checks: Checks = Field(default_factory=Checks)
    requires_confirmation: bool = False
    execution_allowed: bool = False
    transaction: TransactionView | None = None
    intent_id: str | None = None
    classifier_mode: str = "not_called"
    findings: list[Finding] = Field(default_factory=list)
    accounts: list[AccountView] = Field(default_factory=list)
    history: list[HistoryView] = Field(default_factory=list)
    events: list[EventView] = Field(default_factory=list)
    metrics: Metrics | None = None
    evaluation: list[EvaluationRow] = Field(default_factory=list)
    demo_token: str | None = None


class DomainError(Exception):
    def __init__(
        self,
        reason: str,
        category: Category = Category.POLICY_VIOLATION,
        status: int = 409,
    ):
        self.reason, self.category, self.status = reason, category, status
        super().__init__(reason)

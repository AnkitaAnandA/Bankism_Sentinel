from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from app.banking.intent_parser import parse
from app.banking.transfer_service import TransferService
from app.models.database import Account, Beneficiary, Database
from app.models.schemas import (
    AnalyzeRequest,
    Category,
    Checks,
    DomainError,
    Operation,
    Response,
    Risk,
    Verdict,
)
from app.security.llm_classifier import Classifier
from app.security.normalizer import normalize
from app.security.policy_engine import check_policy
from app.security.rule_detector import detect


class RiskEngine:
    def __init__(
        self, db: Database, transfers: TransferService, classifier: Classifier
    ):
        self.db, self.transfers, self.classifier = db, transfers, classifier

    def authorize_read(self, user_id: str) -> bool:
        with self.db.sessions() as s:
            return (
                s.scalar(select(Account.id).where(Account.user_id == user_id))
                is not None
            )

    def validate(self, user_id: str, message: str) -> None:
        parsed = parse(message)
        with self.db.sessions() as s:
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
            if not source:
                raise DomainError("Source account is not authorized", status=403)
            if not payee:
                raise DomainError(
                    "Beneficiary must be registered", Category.UNKNOWN_BENEFICIARY
                )
            check_policy(
                s,
                self.transfers.settings,
                user_id,
                source.id,
                payee.id,
                parsed.amount_minor or 0,
                parsed.currency,
            )

    async def analyze(
        self, user_id: str, body: AnalyzeRequest, request_id: str, prepare: bool = False
    ) -> Response:
        n = normalize(body.message)
        findings = detect(n)
        parsed = parse(n.views[0][1])
        response = Response(
            request_id=request_id,
            reason="Request blocked",
            detected_intent=parsed.operation,
            findings=findings,
        )
        if findings:
            response.threat_category = findings[0].category
            response.risk_level = findings[0].risk
            response.reason = findings[0].evidence
            return response
        classification = await self.classifier.classify(n.views[-1][1])
        if parsed.memo and classification and not classification.is_injection:
            memo_result = await self.classifier.classify(parsed.memo)
            if memo_result is None or memo_result.is_injection:
                classification = memo_result
        response.classifier_mode = self.classifier.mode
        if classification and (
            classification.is_injection
            or classification.risk_level in {Risk.HIGH, Risk.CRITICAL}
        ):
            response.threat_category = classification.threat_category
            response.risk_level = classification.risk_level
            response.reason = classification.evidence
            return response
        authorized = await run_in_threadpool(self.authorize_read, user_id)
        response.policy_checks = Checks(
            injection_safe=classification is not None, account_authorized=authorized
        )
        if parsed.operation == Operation.TRANSFER:
            response.verdict, response.risk_level = Verdict.REVIEW, Risk.MEDIUM
            if classification is None:
                response.threat_category = Category.CLASSIFIER_UNAVAILABLE
                response.reason = (
                    "Classifier unavailable. Transfer cannot be prepared or executed."
                )
                return response
            if parsed.ambiguous or (
                not body.context.intent_id
                and (parsed.amount_minor is None or parsed.beneficiary is None)
            ):
                response.threat_category = Category.AMBIGUOUS_INTENT
                response.reason = (
                    "Please specify one amount and a registered beneficiary."
                )
                return response
            try:
                if prepare or body.context.intent_id:
                    ident, transaction = await run_in_threadpool(
                        self.transfers.prepare, user_id, parsed, body.context.intent_id
                    )
                    response.intent_id, response.transaction = ident, transaction
                    response.requires_confirmation = True
                else:
                    await run_in_threadpool(self.validate, user_id, body.message)
                response.risk_level, response.threat_category = Risk.LOW, Category.NONE
                response.policy_checks.transaction_valid = True
                response.reason = "Valid transfer proposal. Review exact details and confirm before execution."
            except DomainError as exc:
                response.verdict = Verdict.BLOCK
                response.risk_level = Risk.HIGH
                response.threat_category, response.reason = exc.category, exc.reason
            return response
        if parsed.operation in {
            Operation.BALANCE,
            Operation.HISTORY,
            Operation.INFORMATIONAL,
        } and (authorized or parsed.operation == Operation.INFORMATIONAL):
            response.verdict, response.approved, response.risk_level = (
                Verdict.ALLOW,
                True,
                Risk.LOW,
            )
            response.threat_category = (
                Category.NONE if classification else Category.CLASSIFIER_UNAVAILABLE
            )
            response.reason = (
                "Authorized read-only request."
                if parsed.operation != Operation.INFORMATIONAL
                else "Prompt injection is untrusted text attempting to override the application's instructions or authorization."
            )
        else:
            response.verdict, response.risk_level, response.threat_category = (
                Verdict.REVIEW,
                Risk.MEDIUM,
                Category.AMBIGUOUS_INTENT,
            )
            response.reason = "Please ask for a balance, history, or one transfer to a registered beneficiary."
        return response

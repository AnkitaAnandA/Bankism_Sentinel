import asyncio
import json
import tempfile
import uuid
from pathlib import Path

from sqlalchemy import select, update
from starlette.concurrency import run_in_threadpool

from app.banking.intent_parser import parse
from app.banking.transfer_service import TransferService
from app.config import Settings
from app.data.seed import seed
from app.models.database import Account, Database, Intent
from app.models.schemas import (
    AnalyzeRequest,
    DomainError,
    EvaluationRow,
    Operation,
    Response,
    Verdict,
)
from app.security.llm_classifier import MockClassifier
from app.security.risk_engine import RiskEngine

KEYWORDS = ("ignore", "disable", "bypass", "password", "system override")


class OutageClassifier:
    mode = "unavailable"

    async def classify(self, text: str) -> None:
        return None

    def healthy(self) -> bool:
        return False


class Evaluator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache: list[EvaluationRow] | None = None
        self.lock = asyncio.Lock()

    async def run(self) -> list[EvaluationRow]:
        async with self.lock:
            if self.cache is None:
                self.cache = await run_in_threadpool(self.calculate)
            return self.cache

    def calculate(self) -> list[EvaluationRow]:
        rows = json.loads(
            (Path(__file__).resolve().parents[2] / "tests/attack_cases.json").read_text(
                encoding="utf-8"
            )
        )
        output = []
        for configuration in (
            "A Keyword only",
            "B Mock classifier only",
            "C Bankism hybrid + lock",
        ):
            hybrid = configuration.startswith("C")
            hits = false_positives = unauthorized = schema_valid = completed = (
                valid_total
            ) = duplicate_prevented = replay_total = tamper_prevented = tamper_total = 0
            with tempfile.TemporaryDirectory(prefix="bankism-evaluation-") as directory:
                cfg = self.settings.model_copy(
                    update={
                        "database_url": f"sqlite:///{directory}/evaluation.db",
                        "daily_limit": 1000000000,
                    }
                )
                db = Database(cfg.database_url)
                seed(db)
                service = TransferService(db, cfg)
                for case in rows:
                    parsed = parse(case["text"])
                    scenario = case["context"].get("scenario")
                    if hybrid:
                        classifier = (
                            OutageClassifier()
                            if scenario == "classifier_unavailable"
                            else MockClassifier()
                        )
                        result = asyncio.run(
                            RiskEngine(db, service, classifier).analyze(
                                "alice",
                                AnalyzeRequest(message=case["text"]),
                                uuid.uuid4().hex,
                                prepare=True,
                            )
                        )
                        if (
                            scenario in {"parameter_tampering", "replay"}
                            and result.intent_id
                            and result.transaction
                        ):
                            service.confirm(
                                "alice",
                                result.intent_id,
                                result.transaction.integrity_tag,
                                "confirm",
                            )
                            if scenario == "parameter_tampering":
                                tamper_total += 1
                                with db.write() as s:
                                    row = s.get(Intent, result.intent_id)
                                    assert row
                                    row.amount_minor = 1000000
                                try:
                                    service.execution_guard(
                                        "alice", result.intent_id, uuid.uuid4().hex
                                    )
                                except DomainError:
                                    tamper_prevented += 1
                                    result.verdict = Verdict.BLOCK
                            else:
                                replay_total += 1
                                service.execution_guard(
                                    "alice", result.intent_id, uuid.uuid4().hex
                                )
                                try:
                                    service.execution_guard(
                                        "alice", result.intent_id, uuid.uuid4().hex
                                    )
                                except DomainError:
                                    duplicate_prevented += 1
                                    result.verdict = Verdict.BLOCK
                        blocked = result.verdict == Verdict.BLOCK or (
                            scenario == "classifier_unavailable"
                            and not result.intent_id
                        )
                        schema_valid += int(
                            bool(Response.model_validate_json(result.model_dump_json()))
                        )
                    else:
                        classification = asyncio.run(
                            MockClassifier().classify(case["text"])
                        )
                        blocked = (
                            any(k in case["text"].lower() for k in KEYWORDS)
                            if configuration.startswith("A")
                            else classification.is_injection
                        )
                        result = Response(
                            request_id=uuid.uuid4().hex,
                            verdict=Verdict.BLOCK if blocked else Verdict.ALLOW,
                            reason="Isolated unsafe baseline",
                        )
                        schema_valid += int(
                            bool(Response.model_validate_json(result.model_dump_json()))
                        )
                        if scenario == "replay":
                            replay_total += 1
                            if not blocked:
                                self.unsafe_sandbox_debit(
                                    db, parsed.amount_minor or 100000
                                )
                                before = self.sandbox_balance(db)
                                replayed = self.unsafe_sandbox_debit(
                                    db, parsed.amount_minor or 100000
                                )
                                duplicate_prevented += int(
                                    self.sandbox_balance(db) == before
                                )
                                unauthorized += int(replayed)
                        if scenario == "parameter_tampering":
                            tamper_total += 1
                            if not blocked:
                                before = self.sandbox_balance(db)
                                tampered = self.unsafe_sandbox_debit(db, 1000000)
                                tamper_prevented += int(
                                    self.sandbox_balance(db) == before
                                )
                                unauthorized += int(tampered)
                    if case["label"] == "malicious":
                        hits += int(blocked)
                        if (
                            not hybrid
                            and not blocked
                            and parsed.operation == Operation.TRANSFER
                            and scenario not in {"replay", "parameter_tampering"}
                        ):
                            unauthorized += int(
                                self.unsafe_sandbox_debit(
                                    db, parsed.amount_minor or 100000
                                )
                            )
                        elif hybrid and result.intent_id and not scenario:
                            # Missed detection is contained by absence of explicit consent.
                            try:
                                service.execution_guard(
                                    "alice", result.intent_id, uuid.uuid4().hex
                                )
                                unauthorized += 1
                            except DomainError:
                                pass
                    elif case["label"] == "benign":
                        false_positives += int(blocked)
                        valid = (
                            parsed.operation == Operation.TRANSFER
                            and parsed.amount_minor is not None
                            and parsed.beneficiary == "Rahul"
                            and not parsed.ambiguous
                        )
                        if valid:
                            valid_total += 1
                            if not blocked:
                                if hybrid and result.intent_id and result.transaction:
                                    service.confirm(
                                        "alice",
                                        result.intent_id,
                                        result.transaction.integrity_tag,
                                        "confirm",
                                    )
                                    service.execution_guard(
                                        "alice", result.intent_id, uuid.uuid4().hex
                                    )
                                    completed += 1
                                elif not hybrid:
                                    completed += int(
                                        self.unsafe_sandbox_debit(
                                            db, parsed.amount_minor or 0
                                        )
                                    )
                db.engine.dispose()
            malicious = sum(c["label"] == "malicious" for c in rows)
            benign = sum(c["label"] == "benign" for c in rows)
            output.append(
                EvaluationRow(
                    configuration=configuration,
                    dataset_size=len(rows),
                    recall=hits / malicious,
                    false_positive_rate=false_positives / benign,
                    unauthorized_transfers=unauthorized,
                    schema_validity=schema_valid / len(rows),
                    valid_transfer_completion=completed / max(valid_total, 1),
                    duplicate_prevention=duplicate_prevented / max(replay_total, 1),
                    tamper_rejection=tamper_prevented / max(tamper_total, 1),
                )
            )
        return output

    @staticmethod
    def sandbox_balance(db: Database) -> int:
        with db.sessions() as s:
            return (
                s.scalar(
                    select(Account.balance_minor).where(Account.id == "alice-checking")
                )
                or 0
            )

    @staticmethod
    def unsafe_sandbox_debit(db: Database, amount: int) -> bool:
        # Evaluation-only DB; never exposed as an application execution capability.
        with db.write() as s:
            result = s.execute(
                update(Account)
                .where(Account.id == "alice-checking", Account.balance_minor >= amount)
                .values(balance_minor=Account.balance_minor - amount)
            )
            if result.rowcount == 1:
                s.execute(
                    update(Account)
                    .where(Account.id == "rahul-checking")
                    .values(balance_minor=Account.balance_minor + amount)
                )
                return True
            return False

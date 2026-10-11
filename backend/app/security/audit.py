import json
import logging
import time
import uuid

from sqlalchemy import func, select

from app.models.database import Database, SecurityEvent
from app.models.schemas import Category, EventView, Metrics, Response, Risk, Verdict

logger = logging.getLogger("bankism.audit")


class Audit:
    def __init__(self, db: Database):
        self.db = db

    def write(self, response: Response) -> None:
        try:
            with self.db.write() as s:
                # Only server-generated reasons are logged; original user text never is.
                s.add(
                    SecurityEvent(
                        id=str(uuid.uuid4()),
                        request_id=response.request_id,
                        category=response.threat_category,
                        risk=response.risk_level,
                        verdict=response.verdict,
                        evidence=response.reason[:200],
                        timestamp=int(time.time()),
                    )
                )
        except Exception:
            logger.error(
                json.dumps(
                    {
                        "event": "audit_write_failed",
                        "request_id": response.request_id,
                        "verdict": response.verdict,
                        "category": response.threat_category,
                    }
                )
            )

    def events(self, offset: int, limit: int) -> list[EventView]:
        with self.db.sessions() as s:
            rows = s.scalars(
                select(SecurityEvent)
                .order_by(SecurityEvent.timestamp.desc(), SecurityEvent.id)
                .offset(offset)
                .limit(limit)
            ).all()
            return [
                EventView(
                    request_id=r.request_id,
                    category=Category(r.category),
                    risk=Risk(r.risk),
                    verdict=Verdict(r.verdict),
                    evidence=r.evidence,
                    timestamp=r.timestamp,
                )
                for r in rows
            ]

    def metrics(self) -> Metrics:
        with self.db.sessions() as s:
            verdicts = {
                name: count
                for name, count in s.execute(
                    select(SecurityEvent.verdict, func.count()).group_by(
                        SecurityEvent.verdict
                    )
                )
            }
            categories = {
                name: count
                for name, count in s.execute(
                    select(SecurityEvent.category, func.count()).group_by(
                        SecurityEvent.category
                    )
                )
            }
            return Metrics(
                total=sum(verdicts.values()),
                allow=verdicts.get("ALLOW", 0),
                block=verdicts.get("BLOCK", 0),
                review=verdicts.get("REVIEW", 0),
                categories=categories,
            )

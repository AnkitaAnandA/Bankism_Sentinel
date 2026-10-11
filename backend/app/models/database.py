from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    display_name: Mapped[str]
    role: Mapped[str]


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str]
    currency: Mapped[str]
    balance_minor: Mapped[int] = mapped_column(Integer)


class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    beneficiary_name: Mapped[str]
    account_reference: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), index=True
    )
    approved: Mapped[bool] = mapped_column(Boolean)


class Intent(Base):
    __tablename__ = "transaction_intents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    source_account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), index=True
    )
    beneficiary_id: Mapped[str] = mapped_column(
        ForeignKey("beneficiaries.id"), index=True
    )
    amount_minor: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str]
    canonical_payload: Mapped[str] = mapped_column(Text)
    integrity_tag: Mapped[str]
    status: Mapped[str] = mapped_column(String, index=True)
    expires_at: Mapped[int] = mapped_column(Integer, index=True)
    classifier_safe: Mapped[bool] = mapped_column(Boolean)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    intent_id: Mapped[str] = mapped_column(
        ForeignKey("transaction_intents.id"), unique=True
    )
    amount_minor: Mapped[int] = mapped_column(Integer)
    source_account_id: Mapped[str] = mapped_column(
        ForeignKey("accounts.id"), index=True
    )
    beneficiary_id: Mapped[str] = mapped_column(
        ForeignKey("beneficiaries.id"), index=True
    )
    status: Mapped[str]
    idempotency_key: Mapped[str] = mapped_column(String, unique=True)
    timestamp: Mapped[int] = mapped_column(Integer, index=True)


class SecurityEvent(Base):
    __tablename__ = "security_events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    request_id: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str]
    risk: Mapped[str]
    verdict: Mapped[str]
    evidence: Mapped[str]
    timestamp: Mapped[int] = mapped_column(Integer, index=True)


def sqlite_pragmas(connection: Any, _: Any) -> None:
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=10000")
    cursor.close()


class Database:
    def __init__(self, url: str):
        if url.startswith(("postgres://", "postgresql://")):
            url = "postgresql+psycopg://" + url.split("://", 1)[1]
        self.sqlite = url.startswith("sqlite")
        self.engine: Engine = create_engine(
            url,
            connect_args={"check_same_thread": False} if self.sqlite else {},
            pool_pre_ping=True,
        )
        if self.sqlite:
            event.listen(self.engine, "connect", sqlite_pragmas)
        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    @contextmanager
    def write(self) -> Iterator[Session]:
        with self.sessions() as session:
            try:
                if self.sqlite:
                    session.execute(text("BEGIN IMMEDIATE"))
                yield session
                session.commit()
            except BaseException:
                session.rollback()
                raise

    def create(self) -> None:
        Base.metadata.create_all(self.engine)

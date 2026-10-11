import hashlib
import hmac
import json

from app.models.schemas import CanonicalIntent, State

TRANSITIONS: dict[State, set[State]] = {
    State.DRAFT: {State.VALIDATED, State.BLOCKED, State.CANCELLED, State.EXPIRED},
    State.VALIDATED: {
        State.PENDING_CONFIRMATION,
        State.BLOCKED,
        State.CANCELLED,
        State.EXPIRED,
    },
    State.PENDING_CONFIRMATION: {
        State.CONFIRMED,
        State.BLOCKED,
        State.CANCELLED,
        State.EXPIRED,
    },
    State.CONFIRMED: {State.EXECUTED, State.BLOCKED, State.CANCELLED, State.EXPIRED},
    State.EXECUTED: set(),
    State.BLOCKED: set(),
    State.CANCELLED: set(),
    State.EXPIRED: set(),
}


def canonical_bytes(intent: CanonicalIntent) -> bytes:
    return json.dumps(
        intent.model_dump(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")


def sign(intent: CanonicalIntent, key: str) -> str:
    return hmac.new(key.encode(), canonical_bytes(intent), hashlib.sha256).hexdigest()


def verify(intent: CanonicalIntent, tag: str, key: str) -> bool:
    return hmac.compare_digest(sign(intent, key), tag)


def transition(before: State, after: State) -> State:
    if after not in TRANSITIONS[before]:
        raise ValueError(f"Illegal transition {before} → {after}")
    return after

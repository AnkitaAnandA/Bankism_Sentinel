import hashlib
import hmac
import re
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import ORJSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import Response as StarletteResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import Settings
from app.models.schemas import Category, DomainError, Response, Risk, Verdict


@dataclass(frozen=True)
class Identity:
    user_id: str
    role: str


IDENTITIES = {
    "alice": Identity("alice", "customer"),
    "rahul": Identity("rahul", "customer"),
    "analyst": Identity("analyst", "analyst"),
}


def issue_token(user_id: str, settings: Settings) -> str:
    payload = f"{user_id}.{int(time.time()) + 3600}"
    tag = hmac.new(
        settings.session_signing_key.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return payload + "." + tag


def resolve(token: str, settings: Settings) -> Identity:
    try:
        user, expiry, tag = token.split(".")
        expected = hmac.new(
            settings.session_signing_key.encode(),
            f"{user}.{expiry}".encode(),
            hashlib.sha256,
        ).hexdigest()
        if (
            not hmac.compare_digest(tag, expected)
            or int(expiry) <= time.time()
            or user not in IDENTITIES
        ):
            raise ValueError
        return IDENTITIES[user]
    except ValueError as exc:
        raise DomainError("A valid demo session is required", status=401) from exc


def identity(request: Request) -> Identity:
    value = request.headers.get("authorization", "")
    if not value.startswith("Bearer "):
        raise DomainError("Demo login is required", status=401)
    return resolve(value[7:], request.app.state.settings)


def analyst(request: Request) -> Identity:
    user = identity(request)
    if user.role != "analyst":
        raise DomainError("Analyst session required", status=403)
    return user


class JSONCORSMiddleware(CORSMiddleware):
    def preflight_response(self, request_headers: Headers) -> StarletteResponse:
        result = super().preflight_response(request_headers)
        rid = request_headers.get("x-bankism-request-id", "unavailable")
        valid = result.status_code == 200
        body = Response(
            request_id=rid,
            verdict=Verdict.ALLOW if valid else Verdict.BLOCK,
            approved=valid,
            risk_level=Risk.LOW if valid else Risk.HIGH,
            threat_category=Category.NONE if valid else Category.POLICY_VIOLATION,
            reason=(
                "Origin preflight accepted"
                if valid
                else "Origin, method or headers are not permitted"
            ),
        )
        headers = {
            key: value
            for key, value in result.headers.items()
            if key not in {"content-length", "content-type"}
        }
        return ORJSONResponse(
            body.model_dump(mode="json"),
            status_code=result.status_code,
            headers=headers,
        )


class Gateway:
    def __init__(self, app: ASGIApp, settings: Settings):
        self.app, self.settings = app, settings
        self.buckets: OrderedDict[str, tuple[float, float]] = OrderedDict()
        self.origin_regex = (
            re.compile(settings.allowed_origin_regex)
            if settings.allowed_origin_regex
            else None
        )

    def consume(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        tokens, previous = self.buckets.get(key, (float(limit), now))
        tokens = min(float(limit), tokens + (now - previous) * limit / 60)
        ok = tokens >= 1
        self.buckets[key] = (tokens - 1 if ok else tokens, now)
        self.buckets.move_to_end(key)
        if len(self.buckets) > 20000:
            self.buckets.popitem(last=False)
        return ok

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        rid = str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = rid
        headers = {k.decode().lower(): v.decode() for k, v in scope["headers"]}
        scope["headers"] = [
            (key, value)
            for key, value in scope["headers"]
            if key.lower() != b"x-bankism-request-id"
        ] + [(b"x-bankism-request-id", rid.encode())]
        origin = headers.get("origin", "")
        origin_allowed = bool(
            origin
            and (
                origin in [x.strip() for x in self.settings.allowed_origins.split(",")]
                or (self.origin_regex and self.origin_regex.fullmatch(origin))
            )
        )

        async def wrapped_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                if origin_allowed and not any(
                    k.lower() == b"access-control-allow-origin"
                    for k, _ in message["headers"]
                ):
                    message["headers"] = list(message["headers"]) + [
                        (b"access-control-allow-origin", origin.encode()),
                        (b"access-control-expose-headers", b"X-Request-ID"),
                        (b"vary", b"Origin"),
                    ]
                message["headers"] = list(message["headers"]) + [
                    (b"x-request-id", rid.encode()),
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"cache-control", b"no-store"),
                    (
                        b"content-security-policy",
                        b"default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self' http://localhost:8000 https:; img-src 'self' data:; frame-ancestors 'none'",
                    ),
                ]
            await send(message)

        async def reject(reason: str, status: int) -> None:
            result = Response(request_id=rid, reason=reason)
            body = result.model_dump_json().encode()
            await wrapped_send(
                {
                    "type": "http.response.start",
                    "status": status,
                    "headers": [(b"content-type", b"application/json")],
                }
            )
            await wrapped_send({"type": "http.response.body", "body": body})
            audit = getattr(scope["app"].state, "audit", None)
            if audit:
                await run_in_threadpool(audit.write, result)

        path = scope["path"]
        ip = scope.get("client", ("unknown",))[0]
        limit = (
            self.settings.rate_limit_evaluate
            if path == "/api/security/evaluate"
            else self.settings.rate_limit_per_minute
        )
        # Never trust X-Forwarded-For; proxy trust belongs to the server deployment.
        keys = [f"ip:{ip}:{'eval' if path.endswith('evaluate') else 'all'}"]
        if headers.get("authorization"):
            keys.append(
                "session:"
                + hashlib.sha256(headers["authorization"].encode()).hexdigest()
                + (":eval" if path.endswith("evaluate") else "")
            )
        if scope["method"] != "OPTIONS" and not all(
            self.consume(k, max(1, limit)) for k in keys
        ):
            await reject("Rate limit reached. Please wait before retrying.", 429)
            return
        chunks = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunks.extend(message.get("body", b""))
            if len(chunks) > 16384:
                await reject("Request body exceeds 16 KiB", 413)
                return
            if not message.get("more_body", False):
                break
        served = False

        async def replay_receive() -> Message:
            nonlocal served
            if not served:
                served = True
                return {
                    "type": "http.request",
                    "body": bytes(chunks),
                    "more_body": False,
                }
            return await receive()

        await self.app(scope, replay_receive, wrapped_send)

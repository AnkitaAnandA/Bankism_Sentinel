from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.common import respond
from app.banking.queries import accounts_and_history
from app.models.schemas import (
    Category,
    Checks,
    ConfirmRequest,
    ExecuteRequest,
    Operation,
    Response,
    Risk,
    Verdict,
)
from app.security.gateway import identity

router = APIRouter()


@router.post("/api/intents/{intent_id}/confirm")
async def confirm(
    request: Request, intent_id: str, body: ConfirmRequest
) -> ORJSONResponse:
    user = identity(request)
    transaction = await run_in_threadpool(
        request.app.state.transfers.confirm,
        user.user_id,
        intent_id,
        body.integrity_tag,
        body.action,
    )
    return respond(
        request,
        Response(
            request_id=request.state.request_id,
            verdict=Verdict.ALLOW,
            approved=True,
            risk_level=Risk.LOW,
            threat_category=Category.NONE,
            detected_intent=Operation.TRANSFER,
            reason=(
                "Exact proposal confirmed. Execution guard will independently revalidate."
                if body.action == "confirm"
                else "Proposal cancelled."
            ),
            policy_checks=Checks(
                injection_safe=True, account_authorized=True, transaction_valid=True
            ),
            intent_id=intent_id,
            transaction=transaction,
        ),
    )


@router.post("/api/transfers/execute")
async def execute(request: Request, body: ExecuteRequest) -> ORJSONResponse:
    user = identity(request)
    transaction = await run_in_threadpool(
        request.app.state.transfers.execution_guard,
        user.user_id,
        body.intent_id,
        body.idempotency_key,
        request.app.state.classifier.healthy(),
    )
    return respond(
        request,
        Response(
            request_id=request.state.request_id,
            verdict=Verdict.ALLOW,
            approved=True,
            risk_level=Risk.LOW,
            threat_category=Category.NONE,
            detected_intent=Operation.TRANSFER,
            reason="Confirmed transfer executed exactly once through the independent guard.",
            policy_checks=Checks(
                injection_safe=True, account_authorized=True, transaction_valid=True
            ),
            execution_allowed=True,
            intent_id=body.intent_id,
            transaction=transaction,
        ),
    )


@router.get("/api/accounts/balance")
async def balance(request: Request) -> ORJSONResponse:
    user = identity(request)
    accounts, history = await run_in_threadpool(
        accounts_and_history, request.app.state.db, user.user_id
    )
    return respond(
        request,
        Response(
            request_id=request.state.request_id,
            verdict=Verdict.ALLOW,
            approved=True,
            risk_level=Risk.LOW,
            threat_category=Category.NONE,
            detected_intent=Operation.BALANCE,
            reason="Synthetic accounts for the authenticated session.",
            policy_checks=Checks(injection_safe=True, account_authorized=True),
            accounts=accounts,
            history=history,
        ),
    )

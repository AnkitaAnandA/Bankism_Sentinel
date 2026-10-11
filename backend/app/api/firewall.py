from fastapi import APIRouter, Request
from fastapi.responses import ORJSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.common import respond
from app.banking.queries import accounts_and_history
from app.models.schemas import AnalyzeRequest, Operation
from app.security.gateway import identity

router = APIRouter()


@router.post("/api/firewall/analyze")
async def analyze(request: Request, body: AnalyzeRequest) -> ORJSONResponse:
    user = identity(request)
    result = await request.app.state.risk.analyze(
        user.user_id, body, request.state.request_id
    )
    if result.approved and result.detected_intent in {
        Operation.BALANCE,
        Operation.HISTORY,
    }:
        result.accounts, result.history = await run_in_threadpool(
            accounts_and_history, request.app.state.db, user.user_id
        )
    return respond(request, result)


@router.post("/api/intents/prepare")
async def prepare(request: Request, body: AnalyzeRequest) -> ORJSONResponse:
    user = identity(request)
    result = await request.app.state.risk.analyze(
        user.user_id, body, request.state.request_id, prepare=True
    )
    return respond(request, result)

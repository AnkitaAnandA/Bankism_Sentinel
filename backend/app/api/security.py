from fastapi import APIRouter, Query, Request
from fastapi.responses import ORJSONResponse
from starlette.concurrency import run_in_threadpool

from app.api.common import respond
from app.models.schemas import Category, Response, Risk, Verdict
from app.security.gateway import analyst, identity, issue_token

router = APIRouter()


def allowed(request: Request, reason: str) -> Response:
    return Response(
        request_id=request.state.request_id,
        verdict=Verdict.ALLOW,
        approved=True,
        risk_level=Risk.LOW,
        threat_category=Category.NONE,
        reason=reason,
    )


@router.get("/health")
async def health(request: Request) -> ORJSONResponse:
    return ORJSONResponse(
        allowed(request, "Bankism Sentinel ready").model_dump(mode="json")
    )


@router.post("/api/demo/session/{user_id}")
async def demo_session(request: Request, user_id: str) -> ORJSONResponse:
    from app.models.schemas import DomainError
    from app.security.gateway import IDENTITIES

    if user_id not in IDENTITIES:
        raise DomainError("Unknown synthetic demo identity", status=404)
    result = allowed(
        request, "Synthetic demo session; not real banking authentication."
    )
    result.demo_token = issue_token(user_id, request.app.state.settings)
    return respond(request, result)


@router.get("/api/security/events")
async def events(
    request: Request,
    offset: int = Query(default=0, ge=0, le=100000),
    limit: int = Query(default=20, ge=1, le=100),
) -> ORJSONResponse:
    analyst(request)
    result = allowed(request, "Redacted analyst audit events")
    result.events = await run_in_threadpool(
        request.app.state.audit.events, offset, limit
    )
    return respond(request, result)


@router.get("/api/security/metrics")
async def metrics(request: Request) -> ORJSONResponse:
    analyst(request)
    result = allowed(request, "Aggregate synthetic security metrics")
    result.metrics = await run_in_threadpool(request.app.state.audit.metrics)
    return respond(request, result)


@router.post("/api/security/evaluate")
async def evaluate(request: Request) -> ORJSONResponse:
    identity(request)
    result = allowed(
        request,
        "Isolated synthetic comparison; offline classifiers; small dataset feasibility evidence.",
    )
    result.evaluation = await request.app.state.evaluator.run()
    return respond(request, result)

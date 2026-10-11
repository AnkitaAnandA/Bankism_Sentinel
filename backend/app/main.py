import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import ORJSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.exceptions import HTTPException
from starlette.middleware.gzip import GZipMiddleware
from starlette.staticfiles import StaticFiles

from app.api import banking, firewall, security
from app.api.common import respond
from app.banking.transfer_service import TransferService
from app.config import Settings
from app.data.seed import seed
from app.models.database import Database
from app.models.schemas import Category, DomainError, Response
from app.security.audit import Audit
from app.security.gateway import Gateway, JSONCORSMiddleware
from app.security.llm_classifier import LLMClassifier, MockClassifier
from app.security.risk_engine import RiskEngine


def create_app(settings: Settings | None = None) -> FastAPI:
    cfg = settings or Settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        from app.security.evaluation import Evaluator

        db = Database(cfg.database_url)
        await run_in_threadpool(seed, db)
        async with httpx.AsyncClient(timeout=cfg.llm_timeout) as client:
            classifier = (
                LLMClassifier(cfg, client)
                if cfg.llm_api_key and cfg.llm_provider != "mock"
                else MockClassifier()
            )
            application.state.settings, application.state.db = cfg, db
            application.state.classifier = classifier
            application.state.transfers = TransferService(db, cfg)
            application.state.audit = Audit(db)
            application.state.risk = RiskEngine(
                db, application.state.transfers, classifier
            )
            application.state.evaluator = Evaluator(cfg)
            yield
        await run_in_threadpool(db.engine.dispose)

    app = FastAPI(
        title="Bankism Sentinel",
        lifespan=lifespan,
        default_response_class=ORJSONResponse,
        docs_url=None if cfg.env == "production" else "/docs",
        redoc_url=None,
        openapi_url=None if cfg.env == "production" else "/openapi.json",
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        JSONCORSMiddleware,
        allow_origins=[x.strip() for x in cfg.allowed_origins.split(",")],
        allow_origin_regex=cfg.allowed_origin_regex,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["X-Request-ID"],
        allow_credentials=False,
    )
    app.add_middleware(Gateway, settings=cfg)

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError) -> ORJSONResponse:
        return respond(
            request,
            Response(
                request_id=request.state.request_id,
                reason=exc.reason,
                threat_category=exc.category,
            ),
            exc.status,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, exc: RequestValidationError
    ) -> ORJSONResponse:
        return respond(
            request,
            Response(
                request_id=request.state.request_id,
                reason="Request fields are invalid or contain forbidden parameters.",
                threat_category=Category.PARAMETER_TAMPERING,
            ),
            422,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> ORJSONResponse:
        return respond(
            request,
            Response(
                request_id=request.state.request_id,
                reason="Requested operation is unavailable.",
            ),
            exc.status_code,
        )

    @app.exception_handler(Exception)
    async def unexpected(request: Request, exc: Exception) -> ORJSONResponse:
        rid = getattr(request.state, "request_id", "unavailable")
        logging.getLogger("bankism").error(
            '{"event":"request_failed","request_id":"%s"}', rid
        )
        result = respond(
            request,
            Response(
                request_id=rid,
                reason="Secure operation failed. No authorization is granted.",
            ),
            500,
        )
        result.headers["X-Request-ID"] = rid
        return result

    for router in (firewall.router, banking.router, security.router):
        app.include_router(router)
    if cfg.serve_frontend:
        directory = Path(__file__).resolve().parents[2] / "frontend" / "dist"
        app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
    return app


app = create_app()

from fastapi import Request
from fastapi.responses import ORJSONResponse
from starlette.background import BackgroundTask

from app.models.schemas import Response


def respond(request: Request, response: Response, status: int = 200) -> ORJSONResponse:
    return ORJSONResponse(
        response.model_dump(mode="json"),
        status_code=status,
        background=BackgroundTask(request.app.state.audit.write, response),
    )

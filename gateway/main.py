import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from gateway.adapters import ADAPTERS
from gateway.adapters.base import AdapterError
from gateway.config import get_settings
from gateway.logging import configure_logging
from gateway.providers import BarkProvider
from gateway.providers.base import ProviderError
from gateway.security import verify_source_auth

settings = get_settings()
configure_logging(settings.log_level)
logger = logging.getLogger("gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.provider = BarkProvider(
        str(settings.bark_base_url), settings.bark_device_key, settings.bark_timeout_seconds
    )
    yield
    await app.state.provider.close()


app = FastAPI(title="Webhook Bark Gateway", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request_complete",
        extra={
            "request_id": request_id,
            "service": request.path_params.get("service", "system"),
            "status_code": response.status_code,
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return response


@app.get("/healthz", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/hook/{service}/")
async def webhook(service: str, request: Request) -> dict[str, object]:
    adapter = ADAPTERS.get(service)
    if adapter is None:
        raise HTTPException(status_code=404, detail=f"Unknown service '{service}'")

    raw_body = await request.body()
    if len(raw_body) > settings.max_body_bytes:
        raise HTTPException(status_code=413, detail="Webhook payload is too large")
    verify_source_auth(service, request, raw_body, settings)
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Request body must be valid JSON") from None

    try:
        notifications = adapter.transform(payload)
        for notification in notifications:
            await request.app.state.provider.send(notification)
    except (AdapterError, ValidationError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderError as exc:
        logger.exception("provider_delivery_failed", extra={"request_id": request.state.request_id, "service": service})
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    logger.info(
        "webhook_delivered",
        extra={
            "request_id": request.state.request_id,
            "service": service,
            "notification_count": len(notifications),
        },
    )
    return {"ok": True, "service": service, "delivered": len(notifications), "request_id": request.state.request_id}


@app.exception_handler(RequestValidationError)
async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "Invalid request", "errors": exc.errors()})


@app.exception_handler(Exception)
async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "unhandled_error",
        extra={"request_id": getattr(request.state, "request_id", "unknown"), "service": "system"},
    )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

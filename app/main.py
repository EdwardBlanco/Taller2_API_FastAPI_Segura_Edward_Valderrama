import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from .core.config import get_settings
from .core.exceptions import ErrorAplicacion, NoAutenticado
from .core.limiter import limiter
from .routes import api_router

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s",
)
logger = logging.getLogger("biblioteca")

docs_url = None if settings.environment == "prod" else "/docs"
redoc_url = None if settings.environment == "prod" else "/redoc"

app = FastAPI(
    title="API de Biblioteca",
    description="API RESTful para la gestión de biblioteca: autores, categorías, libros, socios y préstamos.",
    version="2.0",
    docs_url=docs_url,
    redoc_url=redoc_url,
)

app.state.limiter = limiter

cors_origins = list(settings.cors_origins)
if settings.environment == "prod" and "*" in cors_origins:
    cors_origins = [orig for orig in cors_origins if orig != "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    response.headers["X-Request-ID"] = request_id

    logger.info(
        "request_id=%s method=%s path=%s status=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response


@app.exception_handler(NoAutenticado)
async def manejar_no_autenticado(request: Request, exc: NoAutenticado):
    return JSONResponse(
        status_code=401,
        content={"detail": exc.mensaje},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(RateLimitExceeded)
async def manejar_rate_limit(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Se superó el límite de peticiones por minuto"},
    )


@app.exception_handler(ErrorAplicacion)
async def manejar_error_aplicacion(request: Request, exc: ErrorAplicacion):
    return JSONResponse(
        status_code=exc.codigo,
        content={"detail": exc.mensaje},
    )


@app.exception_handler(Exception)
async def manejar_error_no_controlado(request: Request, exc: Exception):
    logger.error("Error no controlado: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


app.include_router(api_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)

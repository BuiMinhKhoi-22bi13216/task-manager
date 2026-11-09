import logging
from collections.abc import Awaitable, Callable
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException

from .config import load_settings
from .exceptions import (
    PermissionDeniedError,
    ProjectNotFoundError,
    TaskManagerError,
    TaskNotFoundError,
)
from .routers import auth, external, projects, tasks, users

app = FastAPI(title="Task Manager")
logger = logging.getLogger("uvicorn.error")
settings = load_settings()

# Đăng ký CORS trước middleware thời gian để OPTIONS cũng được đo.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    expose_headers=["X-Process-Time-Ms"],
)


@app.middleware("http")
async def log_request_time(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    start_time = perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    finally:
        duration_ms = (perf_counter() - start_time) * 1000
        logger.info(
            "%s %s status=%s duration_ms=%.3f",
            request.method,
            request.url.path,
            status_code,
            duration_ms,
        )

    response.headers["X-Process-Time-Ms"] = f"{duration_ms:.3f}"
    return response


@app.exception_handler(TaskNotFoundError)
def task_not_found_handler(
    request: Request,
    exc: TaskNotFoundError,
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "TASK_NOT_FOUND",
                "message": str(exc),
                "details": [],
            }
        },
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    details: list[dict[str, object]] = []

    for error in exc.errors():
        details.append(
            {
                "location": list(error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Dữ liệu đầu vào không hợp lệ",
                "details": details,
            }
        },
    )


@app.exception_handler(StarletteHTTPException)
def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": str(exc.detail),
                "details": [],
            }
        },
    )


@app.exception_handler(Exception)
def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "Lỗi nội bộ server",
                "details": [],
            }
        },
    )


app.include_router(tasks.router)
app.include_router(projects.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(external.router)


@app.exception_handler(ProjectNotFoundError)
def project_not_found_handler(
    request: Request, exc: ProjectNotFoundError
) -> JSONResponse:
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc),
                "details": [],
            }
        },
    )


@app.exception_handler(TaskManagerError)
def domain_error_handler(request: Request, exc: TaskManagerError) -> JSONResponse:
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "DOMAIN_ERROR",
                "message": str(exc),
                "details": [],
            }
        },
    )


@app.exception_handler(PermissionDeniedError)
def permission_denied_handler(
    request: Request, exc: PermissionDeniedError
) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "error": {
                "code": "PERMISSION_DENIED",
                "message": "Bạn không có quyền truy cập task này",
                "details": [],
            }
        },
    )
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import ProjectNotFoundError, TaskManagerError, TaskNotFoundError
from .routers import projects, tasks, users

app = FastAPI(title="Task Manager")


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

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..config import load_settings

router = APIRouter(prefix="/external", tags=["External"])
settings = load_settings()


@router.get("/post")
async def get_external_post() -> JSONResponse:
    try:
        async with httpx.AsyncClient(
            timeout=settings.external_api_timeout_seconds
        ) as client:
            response = await client.get(str(settings.external_api_url))
            response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="API bên ngoài phản hồi quá thời gian chờ"
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502, detail="Không lấy được dữ liệu từ API bên ngoài"
        ) from exc

    try:
        return JSONResponse(content=response.json())
    except ValueError as exc:
        raise HTTPException(
            status_code=502, detail="API bên ngoài trả dữ liệu JSON không hợp lệ"
        ) from exc
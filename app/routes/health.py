from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from ..core.dependencies import SessionDep

router = APIRouter(prefix="/health", tags=["Salud"])


@router.get("", summary="Verificar estado del servicio")
def verificar_salud(db: SessionDep):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "error"},
        )


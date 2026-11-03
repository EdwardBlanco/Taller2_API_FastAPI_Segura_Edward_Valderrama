from fastapi import APIRouter

from . import (
    auth,
    autores,
    categorias,
    health,
    libros,
    prestamos,
    reportes,
    socios,
    usuario,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(usuario.router)
api_router.include_router(autores.router)
api_router.include_router(categorias.router)
api_router.include_router(libros.router)
api_router.include_router(socios.router)
api_router.include_router(prestamos.router)
api_router.include_router(reportes.router)

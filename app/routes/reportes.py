from fastapi import APIRouter, Query

from ..controllers import reportes as controlador
from ..core.dependencies import SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.reportes import (
    ReporteAutor,
    ReporteCategoria,
    ReporteLibroMasPrestado,
    ReportePrestamoVencido,
    ReporteResumen,
    ReporteSocioConMultas,
)

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
    },
)


@router.get("/libros-mas-prestados", response_model=list[ReporteLibroMasPrestado], summary="Reporte de libros más prestados")
def reporte_libros_mas_prestados(
    db: SessionDep,
    limite: int = Query(5, ge=1, le=50, description="Cantidad máxima de libros a mostrar"),
):
    return controlador.libros_mas_prestados(db, limite=limite)


@router.get("/categorias", response_model=list[ReporteCategoria], summary="Reporte de libros por categoría")
def reporte_categorias(db: SessionDep):
    return controlador.categorias(db)


@router.get("/prestamos-vencidos", response_model=list[ReportePrestamoVencido], summary="Reporte de préstamos vencidos")
def reporte_prestamos_vencidos(db: SessionDep):
    return controlador.prestamos_vencidos(db)


@router.get("/socios-con-multas", response_model=list[ReporteSocioConMultas], summary="Reporte de socios con multas acumuladas")
def reporte_socios_con_multas(db: SessionDep):
    return controlador.socios_con_multas(db)


@router.get("/autores", response_model=list[ReporteAutor], summary="Reporte de libros y préstamos por autor")
def reporte_autores(db: SessionDep):
    return controlador.autores(db)


@router.get("/resumen", response_model=ReporteResumen, summary="Resumen general de estadísticas de la biblioteca")
def reporte_resumen(db: SessionDep):
    return controlador.resumen(db)

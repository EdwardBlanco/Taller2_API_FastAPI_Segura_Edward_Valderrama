from fastapi import APIRouter, Query, status

from ..controllers import prestamos as controlador
from ..core.dependencies import CurrentUser, PaginacionDep, SessionDep, Staff
from ..schemas.pagina import Pagina
from ..schemas.prestamos import (
    PrestamoCrear,
    PrestamoDetalleLeer,
    PrestamoDevolucion,
    PrestamoLeer,
)

router = APIRouter(
    prefix="/prestamos",
    tags=["Préstamos"]
)


@router.get(
    "",
    response_model=Pagina[PrestamoLeer],
    summary="Listar préstamos de forma paginada",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
    },
)
def listar_prestamos(
    paginacion: PaginacionDep,
    usuario: CurrentUser,
    db: SessionDep,
    estado: str | None = Query(None, pattern="^(activo|vencido|devuelto)$", description="Filtrar por estado"),
    socio_id: int | None = Query(None, description="Filtrar por socio"),
    libro_id: int | None = Query(None, description="Filtrar por libro"),
):
    items, total = controlador.listar(
        db,
        usuario=usuario,
        skip=paginacion.skip,
        limit=paginacion.limit,
        estado=estado,
        socio_id=socio_id,
        libro_id=libro_id,
    )
    return Pagina[PrestamoLeer](
        items=items,
        total=total,
        skip=paginacion.skip,
        limit=paginacion.limit,
    )


@router.get(
    "/{prestamo_id}",
    response_model=PrestamoDetalleLeer,
    summary="Obtener detalle de un préstamo",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Préstamo no encontrado"},
    },
)
def obtener_prestamo(
    prestamo_id: int,
    usuario: CurrentUser,
    db: SessionDep,
):
    return controlador.obtener(db, prestamo_id, usuario)


@router.post(
    "",
    response_model=PrestamoLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo préstamo",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Socio o libro no encontrado"},
        409: {"description": "Préstamo duplicado del mismo libro"},
        422: {"description": "Regla de negocio no cumplida"},
    },
)
def crear_prestamo(
    datos: PrestamoCrear,
    staff: Staff,
    db: SessionDep,
):
    return controlador.crear(db, datos, registrado_por_id=staff.id)


@router.post(
    "/{prestamo_id}/devolucion",
    response_model=PrestamoLeer,
    summary="Registrar la devolución de un préstamo",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Préstamo no encontrado"},
        409: {"description": "Préstamo ya devuelto"},
        422: {"description": "Fecha de devolución inválida"},
    },
)
def registrar_devolucion(
    prestamo_id: int,
    staff: Staff,
    db: SessionDep,
    datos: PrestamoDevolucion | None = None,
):
    datos_devolucion = datos or PrestamoDevolucion()
    return controlador.registrar_devolucion(db, prestamo_id, datos_devolucion)


@router.post(
    "/{prestamo_id}/pago-multa",
    response_model=PrestamoLeer,
    summary="Registrar el pago de la multa de un préstamo",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Préstamo no encontrado"},
        409: {"description": "No tiene multa o ya fue pagada"},
    },
)
def pagar_multa(
    prestamo_id: int,
    staff: Staff,
    db: SessionDep,
):
    return controlador.pagar_multa(db, prestamo_id)

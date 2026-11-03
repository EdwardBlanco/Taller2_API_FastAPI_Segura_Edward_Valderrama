from fastapi import APIRouter, Query, status

from ..controllers import socios as controlador
from ..core.dependencies import (
    Admin,
    CurrentUser,
    PaginacionDep,
    SessionDep,
    Staff,
    requiere_rol,
)
from ..models.usuario import RolUsuario
from ..schemas.pagina import Pagina
from ..schemas.prestamos import PrestamoLeer
from ..schemas.socios import (
    SocioActualizar,
    SocioActualizarPropio,
    SocioCrear,
    SocioLeer,
    SocioMultasRespuesta,
)

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.get(
    "/me",
    response_model=SocioLeer,
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Obtener perfil del socio autenticado",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Socio no encontrado"},
    },
)
def obtener_perfil_propio(usuario: CurrentUser, db: SessionDep):
    return controlador.obtener_propio(db, usuario)


@router.patch(
    "/me",
    response_model=SocioLeer,
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Actualizar perfil del socio autenticado",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Socio no encontrado"},
        422: {"description": "Campos no permitidos o datos inválidos"},
    },
)
def actualizar_perfil_propio(
    datos: SocioActualizarPropio,
    usuario: CurrentUser,
    db: SessionDep,
):
    return controlador.actualizar_propio(db, usuario, datos)


@router.get(
    "/me/prestamos",
    response_model=list[PrestamoLeer],
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Listar préstamos del socio autenticado",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
    },
)
def listar_prestamos_propios(
    usuario: CurrentUser,
    db: SessionDep,
    estado: str | None = Query(None, pattern="^(activo|vencido|devuelto)$", description="Filtrar por estado"),
):
    return controlador.listar_prestamos_socio(db, usuario.socio_id, estado=estado)


@router.get(
    "/me/multas",
    response_model=SocioMultasRespuesta,
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Consultar multas pendientes y total adeudado del socio",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
    },
)
def listar_multas_propias(usuario: CurrentUser, db: SessionDep):
    items, total = controlador.listar_multas_socio(db, usuario.socio_id)
    return SocioMultasRespuesta(prestamos=items, total_adeudado=total)


@router.get(
    "",
    response_model=Pagina[SocioLeer],
    summary="Listar socios de forma paginada",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
    },
)
def listar_socios(
    paginacion: PaginacionDep,
    db: SessionDep,
    staff: Staff,
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
):
    items, total = controlador.listar(
        db,
        skip=paginacion.skip,
        limit=paginacion.limit,
        activo=activo,
    )
    return Pagina[SocioLeer](
        items=items,
        total=total,
        skip=paginacion.skip,
        limit=paginacion.limit,
    )


@router.post(
    "",
    response_model=SocioLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo socio",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        409: {"description": "El correo ya existe"},
        422: {"description": "Datos de socio inválidos"},
    },
)
def crear_socio(datos: SocioCrear, db: SessionDep, staff: Staff):
    return controlador.crear(db, datos)


@router.get(
    "/{socio_id}",
    response_model=SocioLeer,
    summary="Obtener un socio por su identificador",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Socio no encontrado"},
    },
)
def obtener_socio(socio_id: int, db: SessionDep, staff: Staff):
    return controlador.obtener(db, socio_id)


@router.patch(
    "/{socio_id}",
    response_model=SocioLeer,
    summary="Actualizar un socio",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Socio no encontrado"},
        409: {"description": "Conflicto de correo"},
    },
)
def actualizar_socio(
    socio_id: int,
    datos: SocioActualizar,
    db: SessionDep,
    staff: Staff,
):
    return controlador.actualizar(db, socio_id, datos)


@router.delete(
    "/{socio_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar o desactivar un socio",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Socio no encontrado"},
        409: {"description": "Socio con préstamos pendientes"},
    },
)
def eliminar_socio(socio_id: int, db: SessionDep, admin: Admin):
    controlador.eliminar(db, socio_id)


@router.get(
    "/{socio_id}/prestamos",
    response_model=list[PrestamoLeer],
    summary="Listar préstamos de un socio específico",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Socio no encontrado"},
    },
)
def listar_prestamos_socio(
    socio_id: int,
    db: SessionDep,
    staff: Staff,
    estado: str | None = Query(None, pattern="^(activo|vencido|devuelto)$", description="Filtrar por estado"),
):
    return controlador.listar_prestamos_socio(db, socio_id, estado=estado)

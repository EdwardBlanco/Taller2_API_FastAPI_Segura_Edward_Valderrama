from fastapi import APIRouter, Query, status

from ..controllers import usuario as controlador
from ..core.dependencies import Admin, PaginacionDep, SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.pagina import Pagina
from ..schemas.usuario import (
    UsuarioCambiarActivo,
    UsuarioCambiarRol,
    UsuarioCrearAdmin,
    UsuarioRespuesta,
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[requiere_rol(RolUsuario.admin)],
)


@router.get(
    "",
    response_model=Pagina[UsuarioRespuesta],
    summary="Listar usuarios de forma paginada",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
    },
)
def listar_usuarios(
    paginacion: PaginacionDep,
    db: SessionDep,
    rol: RolUsuario | None = Query(None, description="Filtrar por rol"),
    activo: bool | None = Query(None, description="Filtrar por estado activo"),
):
    items, total = controlador.listar(
        db,
        skip=paginacion.skip,
        limit=paginacion.limit,
        rol=rol,
        activo=activo,
    )
    return Pagina[UsuarioRespuesta](
        items=items,
        total=total,
        skip=paginacion.skip,
        limit=paginacion.limit,
    )


@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un usuario bibliotecario o administrador",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        409: {"description": "El correo ya existe"},
        422: {"description": "Datos de usuario inválidos"},
    },
)
def crear_usuario(datos: UsuarioCrearAdmin, db: SessionDep):
    return controlador.crear_personal(db, datos)


@router.patch(
    "/{usuario_id}/rol",
    response_model=UsuarioRespuesta,
    summary="Cambiar rol de un usuario",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Regla de negocio no cumplida"},
    },
)
def cambiar_rol(
    usuario_id: int,
    datos: UsuarioCambiarRol,
    admin: Admin,
    db: SessionDep,
):
    return controlador.cambiar_rol(db, admin, usuario_id, datos.rol)


@router.patch(
    "/{usuario_id}/activo",
    response_model=UsuarioRespuesta,
    summary="Activar o desactivar un usuario",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Regla de negocio no cumplida"},
    },
)
def cambiar_activo(
    usuario_id: int,
    datos: UsuarioCambiarActivo,
    admin: Admin,
    db: SessionDep,
):
    return controlador.cambiar_activo(db, admin, usuario_id, datos.activo)


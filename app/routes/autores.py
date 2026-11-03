from fastapi import APIRouter, Query, status

from ..controllers import autores as controlador
from ..core.dependencies import Admin, PaginacionDep, SessionDep, Staff
from ..schemas.autores import AutorActualizar, AutorCrear, AutorLeer
from ..schemas.libros import LibroLeer
from ..schemas.pagina import Pagina

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.get(
    "",
    response_model=Pagina[AutorLeer],
    summary="Listar autores de forma paginada",
)
def listar_autores(
    paginacion: PaginacionDep,
    db: SessionDep,
    nacionalidad: str | None = Query(None, description="Filtrar por nacionalidad"),
):
    items, total = controlador.listar(
        db,
        skip=paginacion.skip,
        limit=paginacion.limit,
        nacionalidad=nacionalidad,
    )
    return Pagina[AutorLeer](
        items=items,
        total=total,
        skip=paginacion.skip,
        limit=paginacion.limit,
    )


@router.get(
    "/{autor_id}",
    response_model=AutorLeer,
    summary="Obtener un autor por su identificador",
    responses={
        404: {"description": "Autor no encontrado"},
    },
)
def obtener_autor(autor_id: int, db: SessionDep):
    return controlador.obtener(db, autor_id)


@router.post(
    "",
    response_model=AutorLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo autor",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        409: {"description": "El autor ya existe"},
        422: {"description": "Datos de autor inválidos"},
    },
)
def crear_autor(
    datos: AutorCrear,
    staff: Staff,
    db: SessionDep,
):
    return controlador.crear(db, datos)


@router.patch(
    "/{autor_id}",
    response_model=AutorLeer,
    summary="Actualizar un autor existente",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Autor no encontrado"},
        409: {"description": "Conflicto de nombre de autor"},
    },
)
def actualizar_autor(
    autor_id: int,
    datos: AutorActualizar,
    staff: Staff,
    db: SessionDep,
):
    return controlador.actualizar(db, autor_id, datos)


@router.delete(
    "/{autor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un autor",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Autor no encontrado"},
        409: {"description": "Autor con libros asociados"},
    },
)
def eliminar_autor(
    autor_id: int,
    admin: Admin,
    db: SessionDep,
):
    controlador.eliminar(db, autor_id)


@router.get(
    "/{autor_id}/libros",
    response_model=list[LibroLeer],
    summary="Listar todos los libros de un autor",
    responses={
        404: {"description": "Autor no encontrado"},
    },
)
def listar_libros_autor(autor_id: int, db: SessionDep):
    return controlador.listar_libros(db, autor_id)

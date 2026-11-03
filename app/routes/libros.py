from fastapi import APIRouter, Query, status

from ..controllers import libros as controlador
from ..core.dependencies import Admin, PaginacionDep, SessionDep, Staff
from ..schemas.libros import LibroActualizar, LibroCrear, LibroLeer, OrdenLibro
from ..schemas.pagina import Pagina

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.get(
    "",
    response_model=Pagina[LibroLeer],
    summary="Listar libros de forma paginada",
)
def listar_libros(
    paginacion: PaginacionDep,
    db: SessionDep,
    buscar: str | None = Query(None, description="Búsqueda por título"),
    autor: str | None = Query(None, description="Filtrar por nombre de autor"),
    categoria_id: int | None = Query(None, description="Filtrar por ID de categoría"),
    desde: int | None = Query(None, description="Año mínimo de publicación"),
    hasta: int | None = Query(None, description="Año máximo de publicación"),
    orden: OrdenLibro | None = Query(None, description="Criterio de ordenación"),
):
    items, total = controlador.listar(
        db,
        skip=paginacion.skip,
        limit=paginacion.limit,
        buscar=buscar,
        autor=autor,
        categoria_id=categoria_id,
        desde=desde,
        hasta=hasta,
        orden=orden,
    )
    return Pagina[LibroLeer](
        items=items,
        total=total,
        skip=paginacion.skip,
        limit=paginacion.limit,
    )


@router.get(
    "/{libro_id}",
    response_model=LibroLeer,
    summary="Obtener un libro por su identificador",
    responses={
        404: {"description": "Libro no encontrado"},
    },
)
def obtener_libro(libro_id: int, db: SessionDep):
    return controlador.obtener(db, libro_id)


@router.post(
    "",
    response_model=LibroLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo libro",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Autor o categoría no encontrada"},
        409: {"description": "ISBN duplicado"},
        422: {"description": "Datos de libro inválidos"},
    },
)
def crear_libro(
    datos: LibroCrear,
    staff: Staff,
    db: SessionDep,
):
    return controlador.crear(db, datos)


@router.patch(
    "/{libro_id}",
    response_model=LibroLeer,
    summary="Actualizar un libro existente",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Libro no encontrado"},
        409: {"description": "ISBN duplicado"},
        422: {"description": "Regla de negocio no cumplida"},
    },
)
def actualizar_libro(
    libro_id: int,
    datos: LibroActualizar,
    staff: Staff,
    db: SessionDep,
):
    return controlador.actualizar(db, libro_id, datos)


@router.delete(
    "/{libro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un libro",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Libro no encontrado"},
        409: {"description": "Libro con préstamos activos"},
    },
)
def eliminar_libro(
    libro_id: int,
    admin: Admin,
    db: SessionDep,
):
    controlador.eliminar(db, libro_id)

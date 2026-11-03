from fastapi import APIRouter, status

from ..controllers import categorias as controlador
from ..core.dependencies import Admin, PaginacionDep, SessionDep, Staff
from ..schemas.categorias import CategoriaActualizar, CategoriaCrear, CategoriaLeer
from ..schemas.pagina import Pagina

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get(
    "",
    response_model=Pagina[CategoriaLeer],
    summary="Listar categorías de forma paginada",
)
def listar_categorias(paginacion: PaginacionDep, db: SessionDep):
    items, total = controlador.listar(
        db,
        skip=paginacion.skip,
        limit=paginacion.limit,
    )
    return Pagina[CategoriaLeer](
        items=items,
        total=total,
        skip=paginacion.skip,
        limit=paginacion.limit,
    )


@router.get(
    "/{categoria_id}",
    response_model=CategoriaLeer,
    summary="Obtener una categoría por su identificador",
    responses={
        404: {"description": "Categoría no encontrada"},
    },
)
def obtener_categoria(categoria_id: int, db: SessionDep):
    return controlador.obtener(db, categoria_id)


@router.post(
    "",
    response_model=CategoriaLeer,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva categoría",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        409: {"description": "La categoría ya existe"},
        422: {"description": "Datos de categoría inválidos"},
    },
)
def crear_categoria(
    datos: CategoriaCrear,
    staff: Staff,
    db: SessionDep,
):
    return controlador.crear(db, datos)


@router.patch(
    "/{categoria_id}",
    response_model=CategoriaLeer,
    summary="Actualizar una categoría",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Categoría no encontrada"},
        409: {"description": "Conflicto de nombre de categoría"},
    },
)
def actualizar_categoria(
    categoria_id: int,
    datos: CategoriaActualizar,
    staff: Staff,
    db: SessionDep,
):
    return controlador.actualizar(db, categoria_id, datos)


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una categoría",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Categoría no encontrada"},
    },
)
def eliminar_categoria(
    categoria_id: int,
    admin: Admin,
    db: SessionDep,
):
    controlador.eliminar(db, categoria_id)

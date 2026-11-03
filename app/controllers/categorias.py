from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.exceptions import Conflicto, NoEncontrado
from ..models import Categoria
from ..schemas.categorias import CategoriaActualizar, CategoriaCrear


def listar(db: Session, skip: int = 0, limit: int = 10) -> tuple[list[Categoria], int]:
    query = select(Categoria).order_by(Categoria.nombre).offset(skip).limit(limit)
    total = db.scalar(select(func.count(Categoria.id))) or 0
    items = db.scalars(query).all()
    return list(items), total


def obtener(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise NoEncontrado("La categoría no existe")
    return categoria


def crear(db: Session, datos: CategoriaCrear) -> Categoria:
    existente = db.scalar(select(Categoria).where(Categoria.nombre == datos.nombre))
    if existente is not None:
        raise Conflicto("Ya existe una categoría con ese nombre")

    categoria = Categoria(
        nombre=datos.nombre,
        descripcion=datos.descripcion,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def actualizar(db: Session, categoria_id: int, datos: CategoriaActualizar) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise NoEncontrado("La categoría no existe")

    datos_dict = datos.model_dump(exclude_unset=True)
    if "nombre" in datos_dict and datos_dict["nombre"] is not None:
        existente = db.scalar(
            select(Categoria).where(
                Categoria.nombre == datos_dict["nombre"], Categoria.id != categoria_id
            )
        )
        if existente is not None:
            raise Conflicto("Ya existe una categoría con ese nombre")

    for campo, valor in datos_dict.items():
        if valor is not None:
            setattr(categoria, campo, valor)

    db.commit()
    db.refresh(categoria)
    return categoria


def eliminar(db: Session, categoria_id: int) -> None:
    categoria = db.get(Categoria, categoria_id)
    if categoria is None:
        raise NoEncontrado("La categoría no existe")

    db.delete(categoria)
    db.commit()

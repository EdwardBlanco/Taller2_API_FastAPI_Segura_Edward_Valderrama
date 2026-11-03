from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.exceptions import Conflicto, NoEncontrado
from ..models import Autor, Libro
from ..schemas.autores import AutorActualizar, AutorCrear


def listar(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    nacionalidad: str | None = None,
) -> tuple[list[Autor], int]:
    query = select(Autor)
    conteo = select(func.count(Autor.id))

    if nacionalidad:
        termino = f"%{nacionalidad.strip()}%"
        query = query.where(Autor.nacionalidad.ilike(termino))
        conteo = conteo.where(Autor.nacionalidad.ilike(termino))

    total = db.scalar(conteo) or 0
    items = db.scalars(query.order_by(Autor.nombre).offset(skip).limit(limit)).all()
    return list(items), total


def obtener(db: Session, autor_id: int) -> Autor:
    autor = db.get(Autor, autor_id)
    if autor is None:
        raise NoEncontrado("El autor no existe")
    return autor


def crear(db: Session, datos: AutorCrear) -> Autor:
    existente = db.scalar(select(Autor).where(Autor.nombre.ilike(datos.nombre)))
    if existente is not None:
        raise Conflicto("Ya existe un autor con ese nombre")

    autor = Autor(
        nombre=datos.nombre,
        nacionalidad=datos.nacionalidad,
        anio_nacimiento=datos.anio_nacimiento,
    )
    db.add(autor)
    db.commit()
    db.refresh(autor)
    return autor


def actualizar(db: Session, autor_id: int, datos: AutorActualizar) -> Autor:
    autor = db.get(Autor, autor_id)
    if autor is None:
        raise NoEncontrado("El autor no existe")

    datos_dict = datos.model_dump(exclude_unset=True)
    if "nombre" in datos_dict and datos_dict["nombre"] is not None:
        existente = db.scalar(
            select(Autor).where(Autor.nombre.ilike(datos_dict["nombre"]), Autor.id != autor_id)
        )
        if existente is not None:
            raise Conflicto("Ya existe otro autor con ese nombre")

    for campo, valor in datos_dict.items():
        if valor is not None:
            setattr(autor, campo, valor)

    db.commit()
    db.refresh(autor)
    return autor


def eliminar(db: Session, autor_id: int) -> None:
    autor = db.get(Autor, autor_id)
    if autor is None:
        raise NoEncontrado("El autor no existe")

    libro_asociado = db.scalar(
        select(Libro.id).where(Libro.autor_id == autor_id).limit(1)
    )
    if libro_asociado is not None:
        raise Conflicto("No se puede eliminar el autor porque tiene libros asociados")

    db.delete(autor)
    db.commit()


def listar_libros(db: Session, autor_id: int) -> list[Libro]:
    autor = db.get(Autor, autor_id)
    if autor is None:
        raise NoEncontrado("El autor no existe")
    return list(autor.libros)

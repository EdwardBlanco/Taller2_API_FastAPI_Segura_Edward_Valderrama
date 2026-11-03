from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.exceptions import Conflicto, NoEncontrado
from ..models import Prestamo, Socio, Usuario
from ..schemas.socios import SocioActualizar, SocioActualizarPropio, SocioCrear


def listar(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    activo: bool | None = None,
) -> tuple[list[Socio], int]:
    query = select(Socio)
    conteo = select(func.count(Socio.id))

    if activo is not None:
        query = query.where(Socio.activo == activo)
        conteo = conteo.where(Socio.activo == activo)

    total = db.scalar(conteo) or 0
    items = db.scalars(
        query.order_by(Socio.nombre).offset(skip).limit(limit)
    ).all()
    return list(items), total


def obtener(db: Session, socio_id: int) -> Socio:
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise NoEncontrado("El socio no existe")
    return socio


def obtener_propio(db: Session, usuario: Usuario) -> Socio:
    if usuario.socio_id is None:
        raise NoEncontrado("El usuario no tiene un socio vinculado")
    socio = db.get(Socio, usuario.socio_id)
    if socio is None:
        raise NoEncontrado("El socio vinculado no existe")
    return socio


def actualizar_propio(
    db: Session,
    usuario: Usuario,
    datos: SocioActualizarPropio,
) -> Socio:
    if usuario.socio_id is None:
        raise NoEncontrado("El usuario no tiene un socio vinculado")
    socio = db.get(Socio, usuario.socio_id)
    if socio is None:
        raise NoEncontrado("El socio vinculado no existe")

    datos_dict = datos.model_dump(exclude_unset=True)
    for campo, valor in datos_dict.items():
        if valor is not None:
            setattr(socio, campo, valor)
            if campo == "nombre":
                usuario.nombre = valor

    db.commit()
    db.refresh(socio)
    return socio


def crear(db: Session, datos: SocioCrear) -> Socio:
    existente = db.scalar(select(Socio).where(Socio.email == datos.email))
    if existente is not None:
        raise Conflicto("Ya existe un socio con ese correo electrónico")

    socio = Socio(
        nombre=datos.nombre,
        email=datos.email,
        telefono=datos.telefono,
        activo=datos.activo,
    )
    db.add(socio)
    db.commit()
    db.refresh(socio)
    return socio


def actualizar(db: Session, socio_id: int, datos: SocioActualizar) -> Socio:
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise NoEncontrado("El socio no existe")

    datos_dict = datos.model_dump(exclude_unset=True)
    if "email" in datos_dict and datos_dict["email"] is not None:
        existente = db.scalar(
            select(Socio).where(Socio.email == datos_dict["email"], Socio.id != socio_id)
        )
        if existente is not None:
            raise Conflicto("El correo electrónico ya está registrado por otro socio")

    for campo, valor in datos_dict.items():
        if valor is not None:
            setattr(socio, campo, valor)

    if "nombre" in datos_dict and socio.usuario:
        socio.usuario.nombre = datos_dict["nombre"]
    if "email" in datos_dict and socio.usuario:
        socio.usuario.email = datos_dict["email"]
    if "activo" in datos_dict and socio.usuario:
        socio.usuario.activo = datos_dict["activo"]

    db.commit()
    db.refresh(socio)
    return socio


def eliminar(db: Session, socio_id: int) -> None:
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise NoEncontrado("El socio no existe")

    prestamo_activo = db.scalar(
        select(Prestamo.id)
        .where(Prestamo.socio_id == socio_id, Prestamo.fecha_devolucion.is_(None))
        .limit(1)
    )
    if prestamo_activo is not None:
        raise Conflicto("No se puede eliminar el socio porque tiene préstamos sin devolver")

    prestamo_historial = db.scalar(
        select(Prestamo.id).where(Prestamo.socio_id == socio_id).limit(1)
    )
    if prestamo_historial is not None:
        socio.activo = False
        if socio.usuario:
            socio.usuario.activo = False
        db.commit()
    else:
        if socio.usuario:
            db.delete(socio.usuario)
        db.delete(socio)
        db.commit()


def listar_prestamos_socio(db: Session, socio_id: int, estado: str | None = None) -> list[Prestamo]:
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise NoEncontrado("El socio no existe")

    hoy = date.today()
    consulta = select(Prestamo).where(Prestamo.socio_id == socio_id)

    if estado == "activo":
        consulta = consulta.where(
            Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite >= hoy
        )
    elif estado == "vencido":
        consulta = consulta.where(
            Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy
        )
    elif estado == "devuelto":
        consulta = consulta.where(Prestamo.fecha_devolucion.is_not(None))

    consulta = consulta.order_by(Prestamo.fecha_prestamo.desc())
    return list(db.scalars(consulta).all())


def listar_multas_socio(db: Session, socio_id: int) -> tuple[list[Prestamo], float]:
    socio = db.get(Socio, socio_id)
    if socio is None:
        raise NoEncontrado("El socio no existe")

    consulta = (
        select(Prestamo)
        .where(
            Prestamo.socio_id == socio_id,
            Prestamo.multa > 0,
            Prestamo.multa_pagada.is_(False),
        )
        .order_by(Prestamo.fecha_prestamo.desc())
    )
    prestamos = list(db.scalars(consulta).all())
    total = sum(p.multa for p in prestamos)
    return prestamos, round(float(total), 2)

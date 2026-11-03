from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from ..core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from ..core.security import hashear_password
from ..models import RefreshToken, RolUsuario, Socio, Usuario
from ..schemas.usuario import UsuarioCrearAdmin


def listar(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    rol: RolUsuario | None = None,
    activo: bool | None = None,
) -> tuple[list[Usuario], int]:
    consulta = select(Usuario)
    conteo = select(func.count(Usuario.id))

    if rol is not None:
        consulta = consulta.where(Usuario.rol == rol)
        conteo = conteo.where(Usuario.rol == rol)

    if activo is not None:
        consulta = consulta.where(Usuario.activo == activo)
        conteo = conteo.where(Usuario.activo == activo)

    total = db.scalar(conteo) or 0
    items = db.scalars(
        consulta.order_by(Usuario.id.asc()).offset(skip).limit(limit)
    ).all()

    return list(items), total


def crear_personal(db: Session, datos: UsuarioCrearAdmin) -> Usuario:
    email_normalizado = datos.email.strip().lower()

    existente_usuario = db.scalar(
        select(Usuario.id).where(Usuario.email == email_normalizado)
    )
    if existente_usuario is not None:
        raise Conflicto("Ya existe un usuario con ese correo electrónico")

    existente_socio = db.scalar(
        select(Socio.id).where(Socio.email == email_normalizado)
    )
    if existente_socio is not None:
        raise Conflicto("Ya existe un socio con ese correo electrónico")

    usuario = Usuario(
        email=email_normalizado,
        nombre=datos.nombre,
        password_hash=hashear_password(datos.password),
        rol=datos.rol,
        activo=True,
        socio_id=None,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_rol(
    db: Session,
    usuario_admin: Usuario,
    usuario_id: int,
    nuevo_rol: RolUsuario,
) -> Usuario:
    target = db.get(Usuario, usuario_id)
    if target is None:
        raise NoEncontrado("El usuario no existe")

    if target.id == usuario_admin.id and nuevo_rol != RolUsuario.admin:
        raise ReglaNegocio("Un administrador no puede quitarse su propio rol")

    if target.rol == RolUsuario.admin and nuevo_rol != RolUsuario.admin:
        admins_activos = db.scalar(
            select(func.count(Usuario.id)).where(
                Usuario.rol == RolUsuario.admin,
                Usuario.activo.is_(True),
            )
        ) or 0
        if admins_activos <= 1:
            raise ReglaNegocio("Debe existir siempre al menos un administrador activo")

    target.rol = nuevo_rol
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.usuario_id == target.id)
        .values(revocado=True)
    )
    db.commit()
    db.refresh(target)
    return target


def cambiar_activo(
    db: Session,
    usuario_admin: Usuario,
    usuario_id: int,
    activo: bool,
) -> Usuario:
    target = db.get(Usuario, usuario_id)
    if target is None:
        raise NoEncontrado("El usuario no existe")

    if target.id == usuario_admin.id and not activo:
        raise ReglaNegocio("Un administrador no puede desactivarse a sí mismo")

    if target.rol == RolUsuario.admin and target.activo and not activo:
        admins_activos = db.scalar(
            select(func.count(Usuario.id)).where(
                Usuario.rol == RolUsuario.admin,
                Usuario.activo.is_(True),
            )
        ) or 0
        if admins_activos <= 1:
            raise ReglaNegocio("Debe existir siempre al menos un administrador activo")

    target.activo = activo
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.usuario_id == target.id)
        .values(revocado=True)
    )
    db.commit()
    db.refresh(target)
    return target


from datetime import datetime, timedelta, timezone

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.exceptions import Conflicto, CuentaBloqueada, NoAutenticado, Prohibido
from ..core.security import (
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
    hashear_password,
    verificar_password,
)
from ..models import RefreshToken, RolUsuario, Socio, Usuario
from ..schemas.auth import CambiarPasswordEntrada, TokenRespuesta
from ..schemas.usuario import UsuarioRegistro

settings = get_settings()


def registrar_socio(db: Session, datos: UsuarioRegistro) -> Usuario:
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

    socio = Socio(
        nombre=datos.nombre,
        email=email_normalizado,
        telefono=datos.telefono,
        activo=True,
    )
    db.add(socio)
    db.flush()

    usuario = Usuario(
        email=email_normalizado,
        nombre=datos.nombre,
        password_hash=hashear_password(datos.password),
        rol=RolUsuario.socio,
        activo=True,
        socio_id=socio.id,
    )
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


def login(db: Session, form_data: OAuth2PasswordRequestForm) -> TokenRespuesta:
    email = form_data.username.strip().lower()
    usuario = db.scalar(select(Usuario).where(Usuario.email == email))

    if usuario is None:
        raise NoAutenticado("Credenciales inválidas")

    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    ahora = datetime.now(timezone.utc)
    if usuario.bloqueado_hasta is not None and usuario.bloqueado_hasta > ahora:
        raise CuentaBloqueada("Cuenta bloqueada temporalmente")

    if not verificar_password(form_data.password, usuario.password_hash):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= 5:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=15)
        db.commit()
        raise NoAutenticado("Credenciales inválidas")

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None

    access_token, _ = crear_access_token(usuario)
    refresh_token, jti = crear_refresh_token(usuario)

    token_db = RefreshToken(
        jti=jti,
        usuario_id=usuario.id,
        expira_en=ahora + timedelta(days=settings.refresh_token_expire_days),
        revocado=False,
    )
    db.add(token_db)
    db.commit()

    return TokenRespuesta(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


def refrescar_token(db: Session, refresh_token_str: str) -> TokenRespuesta:
    try:
        payload = decodificar_token(refresh_token_str)
    except Exception:
        raise NoAutenticado("Token inválido o vencido")

    if payload.get("type") != "refresh":
        raise NoAutenticado("Tipo de token inválido")

    jti = payload.get("jti")
    if not jti:
        raise NoAutenticado("Token sin identificador")

    token_db = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if token_db is None:
        raise NoAutenticado("Token no encontrado")

    if token_db.revocado:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.usuario_id == token_db.usuario_id)
            .values(revocado=True)
        )
        db.commit()
        raise NoAutenticado("Token revocado")

    ahora = datetime.now(timezone.utc)
    if token_db.expira_en < ahora:
        raise NoAutenticado("Token vencido")

    usuario = db.get(Usuario, token_db.usuario_id)
    if usuario is None:
        raise NoAutenticado("Usuario no encontrado")

    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    token_db.revocado = True

    nuevo_access, _ = crear_access_token(usuario)
    nuevo_refresh, nuevo_jti = crear_refresh_token(usuario)

    nuevo_token_db = RefreshToken(
        jti=nuevo_jti,
        usuario_id=usuario.id,
        expira_en=ahora + timedelta(days=settings.refresh_token_expire_days),
        revocado=False,
    )
    db.add(nuevo_token_db)
    db.commit()

    return TokenRespuesta(
        access_token=nuevo_access,
        refresh_token=nuevo_refresh,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
    )


def logout(db: Session, usuario: Usuario, refresh_token_str: str) -> None:
    try:
        payload = decodificar_token(refresh_token_str)
        jti = payload.get("jti")
        if jti:
            token_db = db.scalar(
                select(RefreshToken).where(
                    RefreshToken.jti == jti,
                    RefreshToken.usuario_id == usuario.id,
                )
            )
            if token_db is not None:
                token_db.revocado = True
                db.commit()
    except Exception:
        pass


def cambiar_password(
    db: Session,
    usuario: Usuario,
    datos: CambiarPasswordEntrada,
) -> Usuario:
    if not verificar_password(datos.password_actual, usuario.password_hash):
        raise NoAutenticado("Credenciales inválidas")

    usuario.password_hash = hashear_password(datos.password_nueva)
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.usuario_id == usuario.id)
        .values(revocado=True)
    )
    db.commit()
    db.refresh(usuario)
    return usuario


from collections.abc import Generator
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
import jwt
from sqlalchemy.orm import Session

from .config import get_settings
from .database import SessionLocal
from .exceptions import NoAutenticado, Prohibido
from ..models.usuario import RolUsuario, Usuario

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


SessionDep = Annotated[Session, Depends(get_db)]
sessionDep = SessionDep


def get_current_user(
    db: SessionDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> Usuario:
    if token is None:
        raise NoAutenticado("Token no proporcionado")
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except jwt.InvalidTokenError:
        raise NoAutenticado("Token inválido o vencido")

    if payload.get("type") != "access":
        raise NoAutenticado("Tipo de token inválido")

    usuario_id = payload.get("sub")
    if not usuario_id:
        raise NoAutenticado("Token sin identificador de usuario")

    try:
        uid = int(usuario_id)
    except (ValueError, TypeError):
        raise NoAutenticado("Identificador de usuario inválido")

    usuario = db.get(Usuario, uid)
    if usuario is None:
        raise NoAutenticado("Usuario no encontrado")

    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def get_optional_current_user(
    db: SessionDep,
    token: Annotated[str | None, Depends(oauth2_scheme)],
) -> Usuario | None:
    if token is None:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
    except jwt.InvalidTokenError:
        return None

    if payload.get("type") != "access":
        return None

    usuario_id = payload.get("sub")
    if not usuario_id:
        return None

    try:
        uid = int(usuario_id)
    except (ValueError, TypeError):
        return None

    usuario = db.get(Usuario, uid)
    if usuario is None or not usuario.activo:
        return None

    return usuario


OptionalCurrentUser = Annotated[Usuario | None, Depends(get_optional_current_user)]


def requiere_rol(*roles: RolUsuario):
    def verificar(usuario: CurrentUser) -> Usuario:
        if usuario.rol not in roles:
            raise Prohibido("No tiene permisos para esta acción")
        return usuario

    return Depends(verificar)


Staff = Annotated[Usuario, requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)]
Admin = Annotated[Usuario, requiere_rol(RolUsuario.admin)]


class Paginacion:
    def __init__(
        self,
        skip: int = Query(0, ge=0, description="Registros a omitir"),
        limit: int = Query(10, ge=1, le=100, description="Límite de registros por página"),
    ):
        self.skip = skip
        self.limit = limit


PaginacionDep = Annotated[Paginacion, Depends()]

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from .config import get_settings

settings = get_settings()
password_hash = PasswordHash.recommended()


def hashear_password(password: str) -> str:
    return password_hash.hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    return password_hash.verify(password, hash_guardado)


def crear_token(usuario, tipo: str, duracion: timedelta) -> tuple[str, str]:
    ahora = datetime.now(timezone.utc)
    jti = str(uuid4())
    rol_valor = usuario.rol.value if hasattr(usuario.rol, "value") else str(usuario.rol)
    payload = {
        "sub": str(usuario.id),
        "rol": rol_valor,
        "type": tipo,
        "iat": ahora,
        "exp": ahora + duracion,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti


def crear_access_token(usuario) -> tuple[str, str]:
    return crear_token(
        usuario,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )


def crear_refresh_token(usuario) -> tuple[str, str]:
    return crear_token(
        usuario,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )


def decodificar_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )


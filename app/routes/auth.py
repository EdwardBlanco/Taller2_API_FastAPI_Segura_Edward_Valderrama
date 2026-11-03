from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from ..controllers import auth as controlador
from ..core.dependencies import CurrentUser, SessionDep
from ..core.limiter import limiter
from ..schemas.auth import CambiarPasswordEntrada, RefreshTokenEntrada, TokenRespuesta
from ..schemas.usuario import UsuarioRegistro, UsuarioRespuesta

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo socio",
    responses={
        409: {"description": "El correo electrónico ya existe"},
        422: {"description": "Datos de registro inválidos"},
        429: {"description": "Límite de peticiones excedido"},
    },
)
@limiter.limit("5/minute")
def registrar_socio(
    request: Request,
    datos: UsuarioRegistro,
    db: SessionDep,
):
    return controlador.registrar_socio(db, datos)


@router.post(
    "/login",
    response_model=TokenRespuesta,
    summary="Iniciar sesión con credenciales",
    responses={
        401: {"description": "Credenciales inválidas"},
        403: {"description": "Usuario inactivo"},
        423: {"description": "Cuenta bloqueada temporalmente"},
        429: {"description": "Límite de peticiones excedido"},
    },
)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep,
):
    return controlador.login(db, form_data)


@router.post(
    "/refresh",
    response_model=TokenRespuesta,
    summary="Renovar access token con refresh token",
    responses={
        401: {"description": "Token inválido, vencido o revocado"},
        403: {"description": "Usuario inactivo"},
    },
)
def refrescar_token(datos: RefreshTokenEntrada, db: SessionDep):
    return controlador.refrescar_token(db, datos.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión y revocar refresh token",
    responses={
        401: {"description": "No autenticado"},
    },
)
def logout(
    datos: RefreshTokenEntrada,
    usuario: CurrentUser,
    db: SessionDep,
):
    controlador.logout(db, usuario, datos.refresh_token)


@router.get(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Obtener perfil del usuario autenticado",
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Usuario inactivo"},
    },
)
def obtener_perfil(usuario: CurrentUser):
    return usuario


@router.patch(
    "/me/password",
    response_model=UsuarioRespuesta,
    summary="Cambiar contraseña del usuario autenticado",
    responses={
        401: {"description": "Contraseña actual incorrecta"},
        422: {"description": "Nueva contraseña no cumple requisitos"},
    },
)
def cambiar_password(
    datos: CambiarPasswordEntrada,
    usuario: CurrentUser,
    db: SessionDep,
):
    return controlador.cambiar_password(db, usuario, datos)


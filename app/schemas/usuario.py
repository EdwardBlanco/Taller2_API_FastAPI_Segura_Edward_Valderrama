from datetime import datetime
import re
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from ..models.usuario import RolUsuario


class UsuarioRegistro(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=3, max_length=100)
    telefono: str | None = Field(default=None)
    password: str = Field(min_length=8, max_length=64)
    confirmar_password: str

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor.title()

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.strip().lower()

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, valor: str | None) -> str | None:
        if valor is not None:
            valor = valor.strip()
            if not valor:
                return None
            if not re.match(r"^[\d\s\+]{7,15}$", valor):
                raise ValueError("El teléfono debe tener entre 7 y 15 caracteres y solo contener dígitos, espacios o +")
            return valor
        return None

    @field_validator("password")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        if not re.search(r"[A-Z]", valor):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", valor):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not re.search(r"\d", valor):
            raise ValueError("La contraseña debe contener al menos un número")
        return valor

    @model_validator(mode="after")
    def verificar_passwords(self) -> Self:
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden")
        return self


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    rol: RolUsuario
    activo: bool
    socio_id: int | None = None
    creado_en: datetime


class UsuarioCrearAdmin(BaseModel):
    email: EmailStr
    nombre: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=64)
    rol: RolUsuario

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, valor: str) -> str:
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío")
        return valor.title()

    @field_validator("email")
    @classmethod
    def normalizar_email(cls, valor: str) -> str:
        return valor.strip().lower()

    @field_validator("password")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        if not re.search(r"[A-Z]", valor):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", valor):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not re.search(r"\d", valor):
            raise ValueError("La contraseña debe contener al menos un número")
        return valor

    @field_validator("rol")
    @classmethod
    def validar_rol(cls, valor: RolUsuario) -> RolUsuario:
        if valor == RolUsuario.socio:
            raise ValueError("No se puede crear usuarios con rol socio desde este endpoint")
        return valor


class UsuarioCambiarRol(BaseModel):
    rol: RolUsuario


class UsuarioCambiarActivo(BaseModel):
    activo: bool


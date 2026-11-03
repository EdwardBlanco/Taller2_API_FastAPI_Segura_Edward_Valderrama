import re
from pydantic import BaseModel, Field, field_validator


class TokenRespuesta(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenEntrada(BaseModel):
    refresh_token: str


class CambiarPasswordEntrada(BaseModel):
    password_actual: str
    password_nueva: str = Field(min_length=8, max_length=64)

    @field_validator("password_nueva")
    @classmethod
    def validar_password(cls, valor: str) -> str:
        if not re.search(r"[A-Z]", valor):
            raise ValueError("La contraseña debe contener al menos una mayúscula")
        if not re.search(r"[a-z]", valor):
            raise ValueError("La contraseña debe contener al menos una minúscula")
        if not re.search(r"\d", valor):
            raise ValueError("La contraseña debe contener al menos un número")
        return valor


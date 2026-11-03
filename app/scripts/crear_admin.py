import getpass

from sqlalchemy import select

from ..core.database import SessionLocal
from ..core.security import hashear_password
from ..models.usuario import RolUsuario, Usuario


def crear_primer_admin() -> None:
    email = input("Email: ").strip().lower()
    nombre = input("Nombre: ").strip().title()
    password = getpass.getpass("Contraseña: ")

    with SessionLocal() as db:
        existente = db.scalar(select(Usuario).where(Usuario.email == email))
        if existente is not None:
            print(f"El usuario con email {email} ya existe.")
            return

        admin = Usuario(
            email=email,
            nombre=nombre,
            password_hash=hashear_password(password),
            rol=RolUsuario.admin,
            activo=True,
            socio_id=None,
        )
        db.add(admin)
        db.commit()
        print(f"Administrador {email} creado exitosamente.")


if __name__ == "__main__":
    crear_primer_admin()


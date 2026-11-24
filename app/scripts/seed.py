"""Script idempotente de datos iniciales (seed) para la biblioteca.

Uso:
    python -m app.scripts.seed
"""

from datetime import date, timedelta

from sqlalchemy import select

from ..core.database import SessionLocal
from ..core.security import hashear_password
from ..models import Autor, Categoria, Libro, Prestamo, RolUsuario, Socio, Usuario


CATEGORIAS_SEED = [
    ("novela", "Obras narrativas extensas de ficción literaria."),
    ("realismo mágico", "Narrativa que integra elementos fantásticos en lo cotidiano."),
    ("ciencia ficción", "Relatos especulativos basados en ciencia y tecnología."),
    ("fantasía", "Mundos imaginarios, mitología y aventuras épicas."),
    ("historia", "Estudios y divulgación sobre el pasado de la humanidad."),
    ("ensayo", "Reflexión crítica, cultural y filosófica."),
    ("cuentos", "Colecciones de relatos breves y ficción corta."),
    ("tecnología", "Ingeniería de software, programación y sistemas."),
]

AUTORES_SEED = [
    ("Gabriel García Márquez", "Colombiana", 1927),
    ("Isabel Allende", "Chilena", 1942),
    ("Jorge Luis Borges", "Argentina", 1899),
    ("Julio Cortázar", "Argentina", 1914),
    ("George Orwell", "Británica", 1903),
    ("Frank Herbert", "Estadounidense", 1920),
    ("Yuval Noah Harari", "Israelí", 1976),
    ("Robert C. Martin", "Estadounidense", 1952),
    ("J. R. R. Tolkien", "Británica", 1892),
    ("Juan Rulfo", "Mexicana", 1917),
]

LIBROS_SEED = [
    {
        "titulo": "Cien Años De Soledad",
        "isbn": "9780307474728",
        "anio_publicacion": 1967,
        "ejemplares": 5,
        "autor": "Gabriel García Márquez",
        "categorias": ["novela", "realismo mágico"],
    },
    {
        "titulo": "El Amor En Los Tiempos Del Cólera",
        "isbn": "9780307387264",
        "anio_publicacion": 1985,
        "ejemplares": 4,
        "autor": "Gabriel García Márquez",
        "categorias": ["novela", "realismo mágico"],
    },
    {
        "titulo": "La Casa De Los Espíritus",
        "isbn": "9781501117015",
        "anio_publicacion": 1982,
        "ejemplares": 3,
        "autor": "Isabel Allende",
        "categorias": ["novela", "realismo mágico"],
    },
    {
        "titulo": "Ficciones",
        "isbn": "9780802130303",
        "anio_publicacion": 1944,
        "ejemplares": 4,
        "autor": "Jorge Luis Borges",
        "categorias": ["cuentos", "fantasía"],
    },
    {
        "titulo": "Rayuela",
        "isbn": "9788437604572",
        "anio_publicacion": 1963,
        "ejemplares": 3,
        "autor": "Julio Cortázar",
        "categorias": ["novela"],
    },
    {
        "titulo": "1984",
        "isbn": "9780451524935",
        "anio_publicacion": 1949,
        "ejemplares": 6,
        "autor": "George Orwell",
        "categorias": ["novela", "ciencia ficción"],
    },
    {
        "titulo": "Rebelión En La Granja",
        "isbn": "9780451526342",
        "anio_publicacion": 1945,
        "ejemplares": 4,
        "autor": "George Orwell",
        "categorias": ["novela", "ensayo"],
    },
    {
        "titulo": "Dune",
        "isbn": "9780441172719",
        "anio_publicacion": 1965,
        "ejemplares": 4,
        "autor": "Frank Herbert",
        "categorias": ["ciencia ficción", "fantasía"],
    },
    {
        "titulo": "Sapiens: De Animales A Dioses",
        "isbn": "9780062316097",
        "anio_publicacion": 2011,
        "ejemplares": 5,
        "autor": "Yuval Noah Harari",
        "categorias": ["historia", "ensayo"],
    },
    {
        "titulo": "Clean Code",
        "isbn": "9780132350884",
        "anio_publicacion": 2008,
        "ejemplares": 4,
        "autor": "Robert C. Martin",
        "categorias": ["tecnología"],
    },
    {
        "titulo": "El Señor De Los Anillos",
        "isbn": "9780544003415",
        "anio_publicacion": 1954,
        "ejemplares": 3,
        "autor": "J. R. R. Tolkien",
        "categorias": ["fantasía", "novela"],
    },
    {
        "titulo": "Pedro Páramo",
        "isbn": "9780802133908",
        "anio_publicacion": 1955,
        "ejemplares": 3,
        "autor": "Juan Rulfo",
        "categorias": ["novela", "realismo mágico"],
    },
]

USUARIOS_STAFF_SEED = [
    ("admin@biblioteca.com", "Administrador Principal", "Admin1234", RolUsuario.admin),
    ("bibliotecario@biblioteca.com", "Sofía Ramírez", "Biblio1234", RolUsuario.bibliotecario),
]

SOCIOS_CON_CUENTA_SEED = [
    ("socio@biblioteca.com", "Ana Torres", "+57 3001234567", "Socio1234"),
    ("carlos.mendez@biblioteca.com", "Carlos Méndez", "+57 3104567890", "Socio1234"),
    ("laura.gomez@biblioteca.com", "Laura Gómez", "+57 3157891234", "Socio1234"),
    ("diego.rojas@biblioteca.com", "Diego Rojas", "+57 3209876543", "Socio1234"),
]

SOCIOS_SOLO_REGISTRO_SEED = [
    ("mariana.silva@biblioteca.com", "Mariana Silva", "+57 3012223344", True),
    ("jorge.perez@biblioteca.com", "Jorge Pérez", "+57 3025556677", False),
]


def openlibrary_cover_url(isbn: str) -> str:
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"


def run_seed() -> None:
    hoy = date.today()

    with SessionLocal() as db:
        # 1. Categorías
        categorias_map: dict[str, Categoria] = {}
        categorias_creadas = 0
        for nombre, descripcion in CATEGORIAS_SEED:
            cat = db.scalar(select(Categoria).where(Categoria.nombre == nombre))
            if cat is None:
                cat = Categoria(nombre=nombre, descripcion=descripcion)
                db.add(cat)
                db.flush()
                categorias_creadas += 1
            categorias_map[nombre] = cat

        # 2. Autores
        autores_map: dict[str, Autor] = {}
        autores_creados = 0
        for nombre, nacionalidad, anio in AUTORES_SEED:
            autor = db.scalar(select(Autor).where(Autor.nombre == nombre))
            if autor is None:
                autor = Autor(nombre=nombre, nacionalidad=nacionalidad, anio_nacimiento=anio)
                db.add(autor)
                db.flush()
                autores_creados += 1
            autores_map[nombre] = autor

        # 3. Libros con portadas
        libros_map: dict[str, Libro] = {}
        libros_creados = 0
        for item in LIBROS_SEED:
            libro = db.scalar(select(Libro).where(Libro.isbn == item["isbn"]))
            cover_url = openlibrary_cover_url(item["isbn"])
            if libro is None:
                libro = Libro(
                    titulo=item["titulo"],
                    isbn=item["isbn"],
                    anio_publicacion=item["anio_publicacion"],
                    ejemplares=item["ejemplares"],
                    autor_id=autores_map[item["autor"]].id,
                    portada_url=cover_url,
                    portada_public_id=None,
                    categorias=[categorias_map[c] for c in item["categorias"]],
                )
                db.add(libro)
                db.flush()
                libros_creados += 1
            elif not libro.portada_url:
                libro.portada_url = cover_url
            libros_map[item["isbn"]] = libro

        # 4. Usuarios staff (admin y bibliotecario)
        usuarios_staff_map: dict[str, Usuario] = {}
        usuarios_creados = 0
        for email, nombre, password, rol in USUARIOS_STAFF_SEED:
            usuario = db.scalar(select(Usuario).where(Usuario.email == email))
            if usuario is None:
                usuario = Usuario(
                    email=email,
                    nombre=nombre,
                    password_hash=hashear_password(password),
                    rol=rol,
                    activo=True,
                    socio_id=None,
                )
                db.add(usuario)
                db.flush()
                usuarios_creados += 1
            usuarios_staff_map[email] = usuario

        # 5. Socios con cuenta de usuario
        socios_map: dict[str, Socio] = {}
        socios_creados = 0
        for email, nombre, telefono, password in SOCIOS_CON_CUENTA_SEED:
            socio = db.scalar(select(Socio).where(Socio.email == email))
            if socio is None:
                socio = Socio(nombre=nombre, email=email, telefono=telefono, activo=True)
                db.add(socio)
                db.flush()
                socios_creados += 1
            socios_map[email] = socio

            usuario = db.scalar(select(Usuario).where(Usuario.email == email))
            if usuario is None:
                usuario = Usuario(
                    email=email,
                    nombre=nombre,
                    password_hash=hashear_password(password),
                    rol=RolUsuario.socio,
                    activo=True,
                    socio_id=socio.id,
                )
                db.add(usuario)
                db.flush()
                usuarios_creados += 1

        # 6. Socios adicionales sin cuenta
        for email, nombre, telefono, activo in SOCIOS_SOLO_REGISTRO_SEED:
            socio = db.scalar(select(Socio).where(Socio.email == email))
            if socio is None:
                socio = Socio(nombre=nombre, email=email, telefono=telefono, activo=activo)
                db.add(socio)
                db.flush()
                socios_creados += 1
            socios_map[email] = socio

        # 7. Préstamos variados (activos, vencidos, devueltos con y sin multa)
        biblio_id = usuarios_staff_map["bibliotecario@biblioteca.com"].id
        prestamos_spec = [
            # Activos
            {
                "isbn": "9780307474728",
                "socio": "socio@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=3),
                "fecha_limite": hoy + timedelta(days=11),
                "fecha_devolucion": None,
                "multa": 0.0,
                "multa_pagada": True,
            },
            {
                "isbn": "9780132350884",
                "socio": "carlos.mendez@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=5),
                "fecha_limite": hoy + timedelta(days=9),
                "fecha_devolucion": None,
                "multa": 0.0,
                "multa_pagada": True,
            },
            {
                "isbn": "9780441172719",
                "socio": "mariana.silva@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=2),
                "fecha_limite": hoy + timedelta(days=12),
                "fecha_devolucion": None,
                "multa": 0.0,
                "multa_pagada": True,
            },
            # Vencidos (sin devolver y fecha_limite pasada)
            {
                "isbn": "9780451524935",
                "socio": "laura.gomez@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=21),
                "fecha_limite": hoy - timedelta(days=7),
                "fecha_devolucion": None,
                "multa": 0.0,
                "multa_pagada": True,
            },
            {
                "isbn": "9780062316097",
                "socio": "diego.rojas@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=18),
                "fecha_limite": hoy - timedelta(days=4),
                "fecha_devolucion": None,
                "multa": 0.0,
                "multa_pagada": True,
            },
            # Devueltos con multa pendiente ($0.50 por día de retraso)
            {
                "isbn": "9780307474728",
                "socio": "carlos.mendez@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=30),
                "fecha_limite": hoy - timedelta(days=16),
                "fecha_devolucion": hoy - timedelta(days=11),
                "multa": 2.50,
                "multa_pagada": False,
            },
            {
                "isbn": "9780544003415",
                "socio": "socio@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=35),
                "fecha_limite": hoy - timedelta(days=21),
                "fecha_devolucion": hoy - timedelta(days=13),
                "multa": 4.00,
                "multa_pagada": False,
            },
            # Devuelto a tiempo sin multa
            {
                "isbn": "9780802130303",
                "socio": "socio@biblioteca.com",
                "fecha_prestamo": hoy - timedelta(days=25),
                "fecha_limite": hoy - timedelta(days=11),
                "fecha_devolucion": hoy - timedelta(days=15),
                "multa": 0.0,
                "multa_pagada": True,
            },
        ]

        prestamos_creados = 0
        for p in prestamos_spec:
            libro_id = libros_map[p["isbn"]].id
            socio_id = socios_map[p["socio"]].id
            existe = db.scalar(
                select(Prestamo).where(
                    Prestamo.libro_id == libro_id,
                    Prestamo.socio_id == socio_id,
                    Prestamo.fecha_prestamo == p["fecha_prestamo"],
                )
            )
            if existe is None:
                db.add(
                    Prestamo(
                        libro_id=libro_id,
                        socio_id=socio_id,
                        fecha_prestamo=p["fecha_prestamo"],
                        fecha_limite=p["fecha_limite"],
                        fecha_devolucion=p["fecha_devolucion"],
                        multa=p["multa"],
                        multa_pagada=p["multa_pagada"],
                        registrado_por_id=biblio_id,
                    )
                )
                prestamos_creados += 1

        db.commit()

    print("Seed completado exitosamente:")
    print(f"  - Categorías nuevas: {categorias_creadas} (total seed: {len(CATEGORIAS_SEED)})")
    print(f"  - Autores nuevos:    {autores_creados} (total seed: {len(AUTORES_SEED)})")
    print(f"  - Libros nuevos:     {libros_creados} (total seed: {len(LIBROS_SEED)})")
    print(f"  - Usuarios nuevos:   {usuarios_creados}")
    print(f"  - Socios nuevos:     {socios_creados}")
    print(f"  - Préstamos nuevos:  {prestamos_creados}")


if __name__ == "__main__":
    run_seed()

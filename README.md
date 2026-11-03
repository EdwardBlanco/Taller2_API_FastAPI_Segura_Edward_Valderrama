# Taller 2 – API REST Segura con FastAPI: Autenticación, Autorización y Migraciones – Biblioteca

## Integrantes
- Edward (Aprendiz ADSO - SENA)

## Descripción
API RESTful para la gestión de una biblioteca con arquitectura en capas (MVC), migraciones versionadas con Alembic, autenticación mediante JWT (Access Token y Refresh Token con rotación), control de acceso basado en roles (RBAC) y por propiedad del recurso, protección contra fuerza bruta y rate limiting con SlowAPI.

## Requisitos Previos
- Python 3.12+ (o compatible)
- PostgreSQL 15+ o Docker
- Git

## Instalación y Preparación del Entorno

1. Clonar el repositorio:
```bash
git clone <URL_DEL_REPOSITORIO>
cd api-taller-biblioteca
```

2. Crear y activar el entorno virtual:
```bash
python -m venv .venv
# En Windows (PowerShell):
.venv\Scripts\Activate.ps1
# En Linux / macOS:
source .venv/bin/activate
```

3. Instalar dependencias de desarrollo y producción:
```bash
pip install -r requirements-dev.txt
```

4. Configurar las variables de entorno:
Copiar `.env.example` a `.env` y ajustar los valores:
```bash
cp .env.example .env
```

## Variables de Entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexión de la API a PostgreSQL | `postgresql+psycopg://postgres:1234@localhost:5432/biblioteca` |
| `TEST_DATABASE_URL` | URL de la base de datos exclusiva para pytest | `postgresql+psycopg://postgres:1234@localhost:5432/biblioteca_test` |
| `SECRET_KEY` | Clave secreta criptográfica (mínimo 32 caracteres) | Generada con `secrets.token_urlsafe(32)` |
| `ALGORITHM` | Algoritmo de firma de los JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del access token en minutos | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Duración del refresh token en días | `7` |
| `CORS_ORIGINS` | Lista JSON de orígenes permitidos para CORS | `["http://localhost:5173"]` |
| `ENVIRONMENT` | Entorno de ejecución (`dev`, `test`, `prod`) | `dev` |

## Migraciones con Alembic

Las tablas de la base de datos se gestionan exclusivamente mediante migraciones de Alembic.

Historial de migraciones del proyecto:
1. `0001_estado_inicial`: Tablas iniciales (`autores`, `categorias`, `libros`, `libro_categoria`, `socios`, `prestamos`).
2. `0002_multa_pagada`: Columna `prestamos.multa_pagada` y migración de datos.
3. `0003_usuarios`: Tabla `usuarios`, tipo enum `rolusuario` y relación 1:1 con socios.
4. `0004_refresh_tokens`: Tabla `refresh_tokens` para persistencia y revocación.
5. `0005_auditoria_prestamos`: Columna `prestamos.registrado_por_id` (FK a usuarios).

Comandos para aplicar o revertir migraciones:
```bash
# Aplicar todas las migraciones:
alembic upgrade head

# Revertir la última migración:
alembic downgrade -1

# Revertir todas las migraciones:
alembic downgrade base

# Ver estado actual:
alembic current
```

## Creación del Primer Administrador

Por seguridad, ningún usuario puede registrarse con rol `admin` desde los endpoints de la API. Se debe ejecutar el script interactivo:

```bash
python -m app.scripts.crear_admin
```

El script solicitará por consola el correo, nombre y contraseña (de forma oculta). Si el correo ya existe, la operación no realizará cambios.

## Ejecución de la API

Para iniciar el servidor de desarrollo:
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
La documentación interactiva OpenAPI estará disponible en:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

*(En entorno `prod`, Swagger UI y ReDoc se deshabilitan automáticamente).*

Con Docker Compose:
```bash
docker compose up -d
```

## Ejecución de Pruebas y Cobertura

Para ejecutar la suite completa de pruebas unitarias y de integración junto con el reporte de cobertura:
```bash
pytest --cov=app --cov-report=term-missing
```

## Roles del Sistema

| Rol | Descripción | Permisos |
|---|---|---|
| `anónimo` | Usuario no autenticado | Registro público, inicio de sesión, consulta pública del catálogo de libros, autores y categorías. |
| `socio` | Persona inscrita vinculada a la tabla `socios` | Consulta y actualización de su propio perfil, préstamos y multas personales. |
| `bibliotecario` | Empleado de la biblioteca | Gestión del catálogo y socios, registro de préstamos, devoluciones, cobro de multas y reportes estadísticos. |
| `admin` | Administrador del sistema | Acceso total, eliminación de recursos y administración completa de usuarios y roles. |

## Matriz de Endpoints y Permisos

Todas las rutas están bajo el prefijo `/api/v1`.

| Método | Endpoint | Descripción | Anónimo | Socio | Bibliotecario | Admin |
|---|---|---|:---:|:---:|:---:|:---:|
| `GET` | `/api/v1/health` | Estado del servicio y conexión a la base de datos | Sí | Sí | Sí | Sí |
| `POST` | `/api/v1/auth/registro` | Registro público de nuevos socios | Sí | Sí | Sí | Sí |
| `POST` | `/api/v1/auth/login` | Inicio de sesión OAuth2 Password Flow | Sí | Sí | Sí | Sí |
| `POST` | `/api/v1/auth/refresh` | Renovación de tokens (rotación) | Sí | Sí | Sí | Sí |
| `POST` | `/api/v1/auth/logout` | Cierre de sesión y revocación del token | No | Sí | Sí | Sí |
| `GET` | `/api/v1/auth/me` | Consulta de perfil del usuario autenticado | No | Sí | Sí | Sí |
| `PATCH` | `/api/v1/auth/me/password` | Cambio de contraseña y revocación de sesiones | No | Sí | Sí | Sí |
| `GET` | `/api/v1/usuarios` | Listado paginado de usuarios | No | No | No | Sí |
| `POST` | `/api/v1/usuarios` | Crear usuario bibliotecario o admin | No | No | No | Sí |
| `PATCH` | `/api/v1/usuarios/{id}/rol` | Modificar rol de un usuario | No | No | No | Sí |
| `PATCH` | `/api/v1/usuarios/{id}/activo` | Activar o desactivar usuario | No | No | No | Sí |
| `GET` | `/api/v1/socios/me` | Datos del socio autenticado | No | Propio | No | No |
| `PATCH` | `/api/v1/socios/me` | Actualizar nombre o teléfono propio | No | Propio | No | No |
| `GET` | `/api/v1/socios/me/prestamos` | Préstamos del socio autenticado | No | Propio | No | No |
| `GET` | `/api/v1/socios/me/multas` | Multas pendientes y deuda total propia | No | Propio | No | No |
| `GET` | `/api/v1/socios` | Listado paginado de socios | No | No | Sí | Sí |
| `POST` | `/api/v1/socios` | Registrar nuevo socio desde administración | No | No | Sí | Sí |
| `GET` | `/api/v1/socios/{id}` | Consultar socio por ID | No | No | Sí | Sí |
| `PATCH` | `/api/v1/socios/{id}` | Actualizar datos de socio por ID | No | No | Sí | Sí |
| `DELETE` | `/api/v1/socios/{id}` | Eliminar socio (o baja lógica si tiene historial) | No | No | No | Sí |
| `GET` | `/api/v1/libros` | Listado paginado con filtros y búsqueda | Sí | Sí | Sí | Sí |
| `GET` | `/api/v1/libros/{id}` | Detalle de un libro | Sí | Sí | Sí | Sí |
| `POST` | `/api/v1/libros` | Crear un nuevo libro | No | No | Sí | Sí |
| `PATCH` | `/api/v1/libros/{id}` | Modificar datos de un libro | No | No | Sí | Sí |
| `DELETE` | `/api/v1/libros/{id}` | Eliminar libro sin préstamos activos | No | No | No | Sí |
| `GET` | `/api/v1/autores` | Listado paginado de autores | Sí | Sí | Sí | Sí |
| `GET` | `/api/v1/autores/{id}` | Detalle de autor | Sí | Sí | Sí | Sí |
| `GET` | `/api/v1/autores/{id}/libros` | Libros escritos por un autor | Sí | Sí | Sí | Sí |
| `POST` | `/api/v1/autores` | Crear autor | No | No | Sí | Sí |
| `PATCH` | `/api/v1/autores/{id}` | Modificar autor | No | No | Sí | Sí |
| `DELETE` | `/api/v1/autores/{id}` | Eliminar autor | No | No | No | Sí |
| `GET` | `/api/v1/categorias` | Listado paginado de categorías | Sí | Sí | Sí | Sí |
| `GET` | `/api/v1/categorias/{id}` | Detalle de categoría | Sí | Sí | Sí | Sí |
| `POST` | `/api/v1/categorias` | Crear categoría | No | No | Sí | Sí |
| `PATCH` | `/api/v1/categorias/{id}` | Modificar categoría | No | No | Sí | Sí |
| `DELETE` | `/api/v1/categorias/{id}` | Eliminar categoría | No | No | No | Sí |
| `GET` | `/api/v1/prestamos` | Listado paginado de préstamos | No | Propio | Sí | Sí |
| `GET` | `/api/v1/prestamos/{id}` | Detalle de préstamo (404 si es de otro socio) | No | Propio | Sí | Sí |
| `POST` | `/api/v1/prestamos` | Registrar préstamo (guarda `registrado_por_id`) | No | No | Sí | Sí |
| `POST` | `/api/v1/prestamos/{id}/devolucion` | Registrar devolución y calcular multa | No | No | Sí | Sí |
| `POST` | `/api/v1/prestamos/{id}/pago-multa` | Registrar pago de multa (409 si ya pagada) | No | No | Sí | Sí |
| `GET` | `/api/v1/reportes/*` | Estadísticas y reportes de gestión | No | No | Sí | Sí |

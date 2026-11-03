from datetime import date, timedelta

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.core.security import hashear_password
from app.models import Autor, Categoria, Libro, Prestamo, RefreshToken, RolUsuario, Socio, Usuario


def crear_admin_db(db: Session) -> Usuario:
    admin = Usuario(
        email="admin@biblioteca.com",
        nombre="Administrador General",
        password_hash=hashear_password("Admin1234*"),
        rol=RolUsuario.admin,
        activo=True,
        socio_id=None,
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return admin


def login_token(client: TestClient, email: str, password: str) -> str:
    res = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def setup_biblioteca(client: TestClient, db: Session):
    admin = crear_admin_db(db)
    token_admin = login_token(client, "admin@biblioteca.com", "Admin1234*")

    res_biblio = client.post(
        "/api/v1/usuarios",
        headers={"Authorization": f"Bearer {token_admin}"},
        json={
            "email": "biblio@biblioteca.com",
            "nombre": "Carlos Bibliotecario",
            "password": "Biblio1234*",
            "rol": "bibliotecario",
        },
    )
    assert res_biblio.status_code == 201
    biblio_data = res_biblio.json()
    token_biblio = login_token(client, "biblio@biblioteca.com", "Biblio1234*")

    res_ana = client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
            "telefono": "+57 3001234567",
        },
    )
    assert res_ana.status_code == 201
    ana_data = res_ana.json()
    token_ana = login_token(client, "ana@example.com", "Password123*")

    res_luis = client.post(
        "/api/v1/auth/registro",
        json={
            "email": "luis@example.com",
            "nombre": "Luis Perez",
            "password": "Password123*",
            "confirmar_password": "Password123*",
            "telefono": "+57 3007654321",
        },
    )
    assert res_luis.status_code == 201
    luis_data = res_luis.json()
    token_luis = login_token(client, "luis@example.com", "Password123*")

    res_autor = client.post(
        "/api/v1/autores",
        headers={"Authorization": f"Bearer {token_biblio}"},
        json={"nombre": "Gabriel Garcia Marquez", "nacionalidad": "Colombiano", "anio_nacimiento": 1927},
    )
    assert res_autor.status_code == 201
    autor_id = res_autor.json()["id"]

    res_cat = client.post(
        "/api/v1/categorias",
        headers={"Authorization": f"Bearer {token_biblio}"},
        json={"nombre": "Realismo Magico", "descripcion": "Obras de realismo magico"},
    )
    assert res_cat.status_code == 201
    categoria_id = res_cat.json()["id"]

    res_libro = client.post(
        "/api/v1/libros",
        headers={"Authorization": f"Bearer {token_biblio}"},
        json={
            "titulo": "Cien Anos de Soledad",
            "isbn": "9780307474728",
            "anio_publicacion": 1967,
            "ejemplares": 5,
            "autor_id": autor_id,
            "categoria_ids": [categoria_id],
        },
    )
    assert res_libro.status_code == 201
    libro_id = res_libro.json()["id"]

    return {
        "admin": admin,
        "token_admin": token_admin,
        "biblio_data": biblio_data,
        "token_biblio": token_biblio,
        "ana_data": ana_data,
        "token_ana": token_ana,
        "luis_data": luis_data,
        "token_luis": token_luis,
        "autor_id": autor_id,
        "categoria_id": categoria_id,
        "libro_id": libro_id,
    }


def test_caso_01_registro_password_invalido(client: TestClient):
    res = client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "abcdefgh",
            "confirmar_password": "abcdefgh",
        },
    )
    assert res.status_code == 422


def test_caso_02_registro_passwords_distintos(client: TestClient):
    res = client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password456*",
        },
    )
    assert res.status_code == 422


def test_caso_03_registro_valido_ana(client: TestClient):
    res = client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    assert res.status_code == 201
    datos = res.json()
    assert datos["rol"] == "socio"
    assert datos["socio_id"] is not None
    assert "password_hash" not in datos
    assert "password" not in datos


def test_caso_04_registro_ana_duplicado(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    res = client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ANA@EXAMPLE.COM",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    assert res.status_code == 409


def test_caso_05_login_contrasena_incorrecta(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "WrongPassword123*"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Credenciales inválidas"


def test_caso_06_login_email_no_existente(client: TestClient):
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "noexiste@example.com", "password": "Password123*"},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Credenciales inválidas"


def test_caso_07_login_correcto_ana(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Password123*"},
    )
    assert res.status_code == 200
    datos = res.json()
    assert "access_token" in datos
    assert "refresh_token" in datos
    assert datos["token_type"] == "bearer"
    assert datos["expires_in"] > 0


def test_caso_08_get_me_sin_token(client: TestClient):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401
    assert "WWW-Authenticate" in res.headers
    assert res.headers["WWW-Authenticate"] == "Bearer"


def test_caso_09_get_me_token_alterado(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    token = login_token(client, "ana@example.com", "Password123*")
    alterado = token[:-1] + ("a" if token[-1] != "a" else "b")
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {alterado}"},
    )
    assert res.status_code == 401


def test_caso_10_get_me_usando_refresh_token_como_bearer(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Password123*"},
    )
    refresh_token = login_res.json()["refresh_token"]
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert res.status_code == 401


def test_caso_11_get_libros_sin_token(client: TestClient, db_session: Session):
    setup_biblioteca(client, db_session)
    res = client.get("/api/v1/libros")
    assert res.status_code == 200
    datos = res.json()
    assert "items" in datos
    assert "total" in datos
    assert "skip" in datos
    assert "limit" in datos


def test_caso_12_post_libros_con_token_ana(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res = client.post(
        "/api/v1/libros",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
        json={
            "titulo": "Otro Libro",
            "isbn": "9781111111111",
            "anio_publicacion": 2020,
            "ejemplares": 2,
            "autor_id": env["autor_id"],
            "categoria_ids": [env["categoria_id"]],
        },
    )
    assert res.status_code == 403


def test_caso_13_post_libros_con_token_bibliotecario(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res = client.post(
        "/api/v1/libros",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "titulo": "Cronica de una Muerte Anunciada",
            "isbn": "9780307387417",
            "anio_publicacion": 1981,
            "ejemplares": 3,
            "autor_id": env["autor_id"],
            "categoria_ids": [env["categoria_id"]],
        },
    )
    assert res.status_code == 201
    assert res.json()["titulo"].lower() == "cronica de una muerte anunciada"


def test_caso_14_delete_libros_con_token_bibliotecario(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res = client.delete(
        f"/api/v1/libros/{env['libro_id']}",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
    )
    assert res.status_code == 403


def test_caso_15_bibliotecario_registra_prestamo_ana(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res = client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["ana_data"]["socio_id"],
            "dias": 14,
        },
    )
    assert res.status_code == 201
    datos = res.json()
    assert datos["registrado_por_id"] == env["biblio_data"]["id"]


def test_caso_16_bibliotecario_registra_prestamo_luis(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res = client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["luis_data"]["socio_id"],
            "dias": 14,
        },
    )
    assert res.status_code == 201


def test_caso_17_get_prestamos_token_ana(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["ana_data"]["socio_id"],
            "dias": 14,
        },
    )
    client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["luis_data"]["socio_id"],
            "dias": 14,
        },
    )

    res = client.get(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
    )
    assert res.status_code == 200
    datos = res.json()
    assert datos["total"] == 1
    assert len(datos["items"]) == 1
    assert datos["items"][0]["socio_id"] == env["ana_data"]["socio_id"]


def test_caso_18_get_prestamos_filtro_otro_socio_token_ana(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["ana_data"]["socio_id"],
            "dias": 14,
        },
    )
    client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["luis_data"]["socio_id"],
            "dias": 14,
        },
    )

    res = client.get(
        f"/api/v1/prestamos?socio_id={env['luis_data']['socio_id']}",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
    )
    assert res.status_code == 200
    datos = res.json()
    assert datos["total"] == 1
    assert datos["items"][0]["socio_id"] == env["ana_data"]["socio_id"]


def test_caso_19_get_prestamo_luis_token_ana(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res_p_luis = client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["luis_data"]["socio_id"],
            "dias": 14,
        },
    )
    luis_prestamo_id = res_p_luis.json()["id"]

    res = client.get(
        f"/api/v1/prestamos/{luis_prestamo_id}",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
    )
    assert res.status_code == 404


def test_caso_20_patch_socios_me_campo_prohibido(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res = client.patch(
        "/api/v1/socios/me",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
        json={"activo": False},
    )
    assert res.status_code == 422


def test_caso_21_post_auth_refresh_ana(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Password123*"},
    )
    refresh_token = login_res.json()["refresh_token"]

    res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res.status_code == 200
    datos = res.json()
    assert "access_token" in datos
    assert "refresh_token" in datos
    assert datos["refresh_token"] != refresh_token


def test_caso_22_post_auth_refresh_reutilizado(client: TestClient, db_session: Session):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Password123*"},
    )
    refresh_token = login_res.json()["refresh_token"]

    res1 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res1.status_code == 200

    res2 = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert res2.status_code == 401

    ana_usuario = db_session.scalar(select(Usuario).where(Usuario.email == "ana@example.com"))
    tokens = db_session.scalars(
        select(RefreshToken).where(RefreshToken.usuario_id == ana_usuario.id)
    ).all()
    assert len(tokens) > 0
    assert all(t.revocado for t in tokens)


def test_caso_23_login_logout_y_refresh(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Password123*"},
    )
    datos = login_res.json()
    access_token = datos["access_token"]
    refresh_token = datos["refresh_token"]

    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_res.status_code == 204

    refresh_res = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 401


def test_caso_24_bloqueo_cuenta_tras_5_intentos(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "luis@example.com",
            "nombre": "Luis Perez",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    for _ in range(5):
        r = client.post(
            "/api/v1/auth/login",
            data={"username": "luis@example.com", "password": "WrongPassword123*"},
        )
        assert r.status_code == 401

    res = client.post(
        "/api/v1/auth/login",
        data={"username": "luis@example.com", "password": "Password123*"},
    )
    assert res.status_code == 423
    assert "bloqueada" in res.json()["detail"].lower()


def test_caso_25_rate_limiting_login(client: TestClient):
    limiter.reset()
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "luis@example.com",
            "nombre": "Luis Perez",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    for i in range(10):
        res = client.post(
            "/api/v1/auth/login",
            data={"username": "luis@example.com", "password": "WrongPassword123*"},
        )
        assert res.status_code in [401, 423]

    res_11 = client.post(
        "/api/v1/auth/login",
        data={"username": "luis@example.com", "password": "Password123*"},
    )
    assert res_11.status_code == 429
    limiter.reset()


def test_caso_26_usuario_desactivado_access_token_invalido(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res_deactivate = client.patch(
        f"/api/v1/usuarios/{env['luis_data']['id']}/activo",
        headers={"Authorization": f"Bearer {env['token_admin']}"},
        json={"activo": False},
    )
    assert res_deactivate.status_code == 200

    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {env['token_luis']}"},
    )
    assert res.status_code == 403
    assert res.json()["detail"] == "Usuario inactivo"


def test_caso_27_admin_se_cambia_su_propio_rol(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res = client.patch(
        f"/api/v1/usuarios/{env['admin'].id}/rol",
        headers={"Authorization": f"Bearer {env['token_admin']}"},
        json={"rol": "socio"},
    )
    assert res.status_code == 422


def test_caso_28_reportes_resumen_ana_y_bibliotecario(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res_ana = client.get(
        "/api/v1/reportes/resumen",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
    )
    assert res_ana.status_code == 403

    res_biblio = client.get(
        "/api/v1/reportes/resumen",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
    )
    assert res_biblio.status_code == 200
    datos = res_biblio.json()
    assert "total_libros" in datos
    assert "total_ejemplares" in datos


def test_caso_29_30_regla_r11_multa_y_pago(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    fecha_hace_20_dias = date.today() - timedelta(days=20)

    res_prestamo = client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["ana_data"]["socio_id"],
            "fecha_prestamo": str(fecha_hace_20_dias),
            "dias": 7,
        },
    )
    assert res_prestamo.status_code == 201
    prestamo_id = res_prestamo.json()["id"]

    res_dev = client.post(
        f"/api/v1/prestamos/{prestamo_id}/devolucion",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={"fecha_devolucion": str(date.today())},
    )
    assert res_dev.status_code == 200
    datos_dev = res_dev.json()
    assert datos_dev["multa"] == 6.5
    assert datos_dev["multa_pagada"] is False

    res_nuevo = client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["ana_data"]["socio_id"],
            "dias": 14,
        },
    )
    assert res_nuevo.status_code == 422
    assert "multas pendientes" in res_nuevo.json()["detail"].lower()

    res_pago = client.post(
        f"/api/v1/prestamos/{prestamo_id}/pago-multa",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
    )
    assert res_pago.status_code == 200
    assert res_pago.json()["multa_pagada"] is True

    res_repetir = client.post(
        "/api/v1/prestamos",
        headers={"Authorization": f"Bearer {env['token_biblio']}"},
        json={
            "libro_id": env["libro_id"],
            "socio_id": env["ana_data"]["socio_id"],
            "dias": 14,
        },
    )
    assert res_repetir.status_code == 201


def test_caso_31_health_endpoint(client: TestClient):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "ok"}


def test_socios_me_endpoints(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res_me = client.get(
        "/api/v1/socios/me",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "ana@example.com"

    res_patch = client.patch(
        "/api/v1/socios/me",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
        json={"nombre": "Ana Maria Torres", "telefono": "+57 3110000000"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["nombre"] == "Ana Maria Torres"

    res_prestamos = client.get(
        "/api/v1/socios/me/prestamos",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
    )
    assert res_prestamos.status_code == 200

    res_multas = client.get(
        "/api/v1/socios/me/multas",
        headers={"Authorization": f"Bearer {env['token_ana']}"},
    )
    assert res_multas.status_code == 200
    assert "total_adeudado" in res_multas.json()


def test_cambiar_password_me(client: TestClient):
    client.post(
        "/api/v1/auth/registro",
        json={
            "email": "ana@example.com",
            "nombre": "Ana Torres",
            "password": "Password123*",
            "confirmar_password": "Password123*",
        },
    )
    token = login_token(client, "ana@example.com", "Password123*")
    res = client.patch(
        "/api/v1/auth/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password_actual": "Password123*", "password_nueva": "NewPassword123*"},
    )
    assert res.status_code == 200

    res_fail = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "Password123*"},
    )
    assert res_fail.status_code == 401

    res_ok = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "NewPassword123*"},
    )
    assert res_ok.status_code == 200


def test_admin_gestion_usuarios(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    res_list = client.get(
        "/api/v1/usuarios",
        headers={"Authorization": f"Bearer {env['token_admin']}"},
    )
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 3

    res_rol = client.patch(
        f"/api/v1/usuarios/{env['biblio_data']['id']}/rol",
        headers={"Authorization": f"Bearer {env['token_admin']}"},
        json={"rol": "admin"},
    )
    assert res_rol.status_code == 200
    assert res_rol.json()["rol"] == "admin"


def test_reportes_completos(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    token = env["token_biblio"]
    for path in [
        "/api/v1/reportes/libros-mas-prestados",
        "/api/v1/reportes/categorias",
        "/api/v1/reportes/prestamos-vencidos",
        "/api/v1/reportes/socios-con-multas",
        "/api/v1/reportes/autores",
        "/api/v1/reportes/resumen",
    ]:
        res = client.get(path, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200


def test_autores_categorias_libros_crud(client: TestClient, db_session: Session):
    env = setup_biblioteca(client, db_session)
    token_biblio = env["token_biblio"]
    token_admin = env["token_admin"]

    res_a = client.get(f"/api/v1/autores/{env['autor_id']}")
    assert res_a.status_code == 200
    res_al = client.get(f"/api/v1/autores/{env['autor_id']}/libros")
    assert res_al.status_code == 200

    res_patch_a = client.patch(
        f"/api/v1/autores/{env['autor_id']}",
        headers={"Authorization": f"Bearer {token_biblio}"},
        json={"nacionalidad": "Colombiana"},
    )
    assert res_patch_a.status_code == 200

    res_c = client.get(f"/api/v1/categorias/{env['categoria_id']}")
    assert res_c.status_code == 200
    res_patch_c = client.patch(
        f"/api/v1/categorias/{env['categoria_id']}",
        headers={"Authorization": f"Bearer {token_biblio}"},
        json={"descripcion": "Nueva descripcion"},
    )
    assert res_patch_c.status_code == 200

    res_l = client.get(f"/api/v1/libros/{env['libro_id']}")
    assert res_l.status_code == 200
    res_patch_l = client.patch(
        f"/api/v1/libros/{env['libro_id']}",
        headers={"Authorization": f"Bearer {token_biblio}"},
        json={"ejemplares": 10},
    )
    assert res_patch_l.status_code == 200

    res_del_l = client.delete(
        f"/api/v1/libros/{env['libro_id']}",
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_del_l.status_code == 204


def test_caso_32_alembic_downgrade_y_upgrade():
    import subprocess
    import sys
    r1 = subprocess.run([sys.executable, "-m", "alembic", "downgrade", "base"], capture_output=True, text=True)
    assert r1.returncode == 0
    r2 = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], capture_output=True, text=True)
    assert r2.returncode == 0



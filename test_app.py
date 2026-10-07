import pytest
from ecosoporte import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_public_routes(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "EcoSoporte Digital" in res.get_data(as_text=True)

    res_login = client.get("/login")
    assert res_login.status_code == 200
    assert "Bienvenido a EcoSoporte Digital" in res_login.get_data(as_text=True)

def test_login_admin(client):
    res = client.post("/login", data={
        "email": "admin@ecosoporte.com",
        "password": "EcoSoporte2026!"
    }, follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Hola, Luis Neira" in html or "Administrador" in html
    assert "Solicitudes Recientes" in html

def test_login_soporte(client):
    res = client.post("/login", data={
        "email": "soporte@ecosoporte.com",
        "password": "Soporte2026!"
    }, follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "SOPORTE TI" in html
    assert "Tickets Asignados" in html or "Solicitudes Disponibles" in html

def test_login_usuario(client):
    res = client.post("/login", data={
        "email": "usuario@ecosoporte.com",
        "password": "Usuario2026!"
    }, follow_redirects=True)
    assert res.status_code == 200
    html = res.get_data(as_text=True)
    assert "Mis Solicitudes" in html
    assert "Crear solicitud" in html

def test_unauthorized_access(client):
    # Log in as normal user
    client.post("/login", data={
        "email": "usuario@ecosoporte.com",
        "password": "Usuario2026!"
    })
    # Try to access admin users page
    res = client.get("/admin/users")
    assert res.status_code == 403
    html = res.get_data(as_text=True)
    assert "Acceso Denegado" in html
    assert "Volver al inicio" in html

def test_logout(client):
    client.post("/login", data={
        "email": "admin@ecosoporte.com",
        "password": "EcoSoporte2026!"
    })
    res = client.get("/logout", follow_redirects=True)
    assert res.status_code == 200
    assert "Iniciar sesión" in res.get_data(as_text=True)

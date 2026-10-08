import pytest
from ecosoporte import create_app
from ecosoporte.database import get_db

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
    client.post("/login", data={
        "email": "usuario@ecosoporte.com",
        "password": "Usuario2026!"
    })
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

def test_database_connectivity(app):
    with app.app_context():
        db = get_db()
        roles = db.execute("SELECT COUNT(*) c FROM roles").fetchone()["c"]
        assert roles >= 3
        users = db.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"]
        assert users >= 3
        db.close()

def test_search_tickets(client, app):
    client.post("/login", data={
        "email": "admin@ecosoporte.com",
        "password": "EcoSoporte2026!"
    })

    # Create a test ticket
    with app.app_context():
        db = get_db()
        usr = db.execute("SELECT id FROM usuarios WHERE email='admin@ecosoporte.com'").fetchone()
        estado = db.execute("SELECT id FROM estados_ticket WHERE name='NUEVO'").fetchone()["id"]
        db.execute("""
            INSERT INTO tickets(titulo, descripcion, usuario_id, estado_id)
            VALUES('Problema con Impresora Laser HP', 'La impresora no responde al enviar trabajos', ?, ?)
        """, (usr["id"], estado))
        db.commit()
        db.close()

    # Search ticket by keyword 'Impresora'
    res = client.get("/tickets/?q=Impresora")
    assert res.status_code == 200
    assert "Problema con Impresora Laser HP" in res.get_data(as_text=True)

    # Search non-existent
    res_none = client.get("/tickets/?q=NonExistentKeywordXYZ")
    assert res_none.status_code == 200
    assert "No se encontraron solicitudes" in res_none.get_data(as_text=True)

def test_search_users(client):
    client.post("/login", data={
        "email": "admin@ecosoporte.com",
        "password": "EcoSoporte2026!"
    })
    res = client.get("/admin/users?q=Luis")
    assert res.status_code == 200
    assert "admin@ecosoporte.com" in res.get_data(as_text=True)

def test_search_companies(client, app):
    client.post("/login", data={
        "email": "admin@ecosoporte.com",
        "password": "EcoSoporte2026!"
    })
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO empresas(nombre, nit, sector, ciudad) VALUES('TecnoCorp S.A.S.', '900123456', 'Tecnología', 'Bogotá')")
        db.commit()
        db.close()

    res = client.get("/companies/?q=TecnoCorp")
    assert res.status_code == 200
    assert "TecnoCorp S.A.S." in res.get_data(as_text=True)

def test_search_equipos(client, app):
    client.post("/login", data={
        "email": "admin@ecosoporte.com",
        "password": "EcoSoporte2026!"
    })
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO equipos(nombre, tipo, marca, serial) VALUES('Servidor-Rack-01', 'Servidor', 'Dell PowerEdge', 'SN-DELL-9988')")
        db.commit()
        db.close()

    res = client.get("/equipos?q=PowerEdge")
    assert res.status_code == 200
    assert "Servidor-Rack-01" in res.get_data(as_text=True)

def test_search_servicios(client):
    client.post("/login", data={
        "email": "usuario@ecosoporte.com",
        "password": "Usuario2026!"
    })
    res = client.get("/servicios?q=Mantenimiento")
    assert res.status_code == 200
    assert "Mantenimiento Preventivo" in res.get_data(as_text=True)

def test_search_base_conocimiento(client):
    client.post("/login", data={
        "email": "usuario@ecosoporte.com",
        "password": "Usuario2026!"
    })
    res = client.get("/base-conocimiento?q=WiFi")
    assert res.status_code == 200
    assert "WiFi" in res.get_data(as_text=True)

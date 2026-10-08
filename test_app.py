import pytest
from app import create_app

@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True)
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_public_routes(client):
    res = client.get('/')
    assert res.status_code == 200
    res = client.get('/login')
    assert res.status_code == 200
    assert b'EcoSoporte Digital' in res.data

def test_admin_flow(client):
    # Admin Login
    res = client.post('/login', data={'email': 'admin@ecosoportedigital.com', 'password': 'EcoSoporteAdmin2026!'}, follow_redirects=True)
    assert res.status_code == 200
    assert b'Dashboard administrador' in res.data or b'EcoSoporte' in res.data

    # Admin Endpoints
    for path in ['/admin/dashboard', '/soporte-ti', '/equipos', '/servicios', '/reportes', '/ans-sla', '/base-conocimiento', '/configuracion', '/admin/users', '/companies/', '/tickets/']:
        res = client.get(path)
        assert res.status_code == 200, f"Failed on {path}"
        assert b'app.css' in res.data
        assert b'logo.png' in res.data

def test_access_denied_for_client(client):
    # Create client or test unauth access
    res = client.get('/admin/dashboard')
    assert res.status_code == 302 # Redirects to login when not authenticated

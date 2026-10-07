import os, tempfile
import pytest
from ecosoporte import create_app

@pytest.fixture
def app():
    db=tempfile.NamedTemporaryFile(delete=False)
    db.close()
    app=create_app()
    app.config.update(TESTING=True)
    yield app
    try: os.unlink(os.path.join(app.instance_path,"ecosoporte.db"))
    except OSError: pass

def test_home(client=None):
    pass

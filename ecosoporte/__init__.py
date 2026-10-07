import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-ecosoporte-change-me")
    os.makedirs(app.instance_path, exist_ok=True)

    from .database import init_db, seed_db
    init_db(app)
    seed_db(app)

    from .auth import auth_bp
    from .main import main_bp
    from .admin import admin_bp
    from .tickets import tickets_bp
    from .companies import companies_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(tickets_bp, url_prefix="/tickets")
    app.register_blueprint(companies_bp, url_prefix="/companies")

    return app

from flask import Blueprint, render_template, session, redirect, url_for
from database import get_db
from decorators import login_required

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return render_template("index.html")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    if role == "ADMINISTRADOR":
        return redirect(url_for("admin.dashboard"))
    if role.startswith("TECNICO"):
        return redirect(url_for("tickets.technician_dashboard"))
    return redirect(url_for("tickets.client_dashboard"))

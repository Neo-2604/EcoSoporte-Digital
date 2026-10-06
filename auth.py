from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from .database import get_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        db = get_db()
        user = db.execute("""SELECT u.*, r.name role FROM usuarios u
                            JOIN roles r ON r.id=u.role_id WHERE lower(u.email)=?""",(email,)).fetchone()
        db.close()
        if not user or not check_password_hash(user["password_hash"], password):
            flash("Correo o contraseña incorrectos.", "danger")
        elif user["estado"] != "ACTIVO":
            flash("Tu cuenta no está activa.", "danger")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["nombre"]
            session["role"] = user["role"]
            session["empresa_id"] = user["empresa_id"]
            return redirect(url_for("main.dashboard"))
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("main.home"))

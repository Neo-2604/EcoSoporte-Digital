from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from .database import get_db
from .decorators import role_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/")
@admin_bp.route("/inicio")
@role_required("ADMINISTRADOR")
def index():
    return redirect(url_for("main.inicio"))

@admin_bp.route("/users", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def users():
    db = get_db()
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "")

        role_row = db.execute("SELECT id FROM roles WHERE name=?", (role,)).fetchone()
        if role_row and nombre and email and password:
            try:
                db.execute("INSERT INTO usuarios(nombre, email, password_hash, role_id) VALUES(?,?,?,?)",
                           (nombre, email, generate_password_hash(password), role_row["id"]))
                db.commit()
                flash("Usuario registrado correctamente.", "success")
            except Exception:
                flash("No fue posible registrar el usuario. El correo electrónico ya existe.", "danger")
        else:
            flash("Todos los campos obligatorios deben ser diligenciados.", "warning")

    query_str = request.args.get("q", "").strip()
    if query_str:
        pattern = f"%{query_str}%"
        users_list = db.execute("""
            SELECT u.*, r.name role, e.nombre empresa
            FROM usuarios u
            JOIN roles r ON r.id=u.role_id
            LEFT JOIN empresas e ON e.id=u.empresa_id
            WHERE u.nombre LIKE ? OR u.email LIKE ? OR r.name LIKE ? OR e.nombre LIKE ?
            ORDER BY u.id DESC
        """, (pattern, pattern, pattern, pattern)).fetchall()
    else:
        users_list = db.execute("""
            SELECT u.*, r.name role, e.nombre empresa
            FROM usuarios u
            JOIN roles r ON r.id=u.role_id
            LEFT JOIN empresas e ON e.id=u.empresa_id
            ORDER BY u.id DESC
        """).fetchall()

    roles_list = db.execute("SELECT name FROM roles ORDER BY id").fetchall()
    db.close()
    return render_template("users.html", users=users_list, roles=roles_list, search_query=query_str)

@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@role_required("ADMINISTRADOR")
def toggle_user(user_id):
    db = get_db()
    row = db.execute("SELECT estado FROM usuarios WHERE id=?", (user_id,)).fetchone()
    if row:
        new_state = "INACTIVO" if row["estado"] == "ACTIVO" else "ACTIVO"
        db.execute("UPDATE usuarios SET estado=? WHERE id=?", (new_state, user_id))
        db.commit()
        flash(f"Estado del usuario actualizado a {new_state}.", "success")
    db.close()
    return redirect(url_for("admin.users"))

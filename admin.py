from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from .database import get_db
from .decorators import role_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@role_required("ADMINISTRADOR")
def dashboard():
    db=get_db()
    metrics={
        "empresas": db.execute("SELECT COUNT(*) c FROM empresas").fetchone()["c"],
        "usuarios": db.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"],
        "tecnicos": db.execute("SELECT COUNT(*) c FROM usuarios u JOIN roles r ON r.id=u.role_id WHERE r.name LIKE 'TECNICO%'").fetchone()["c"],
        "tickets": db.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"],
        "abiertos": db.execute("""SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id=t.estado_id
                                  WHERE e.name NOT IN ('CERRADO','RESUELTO')""").fetchone()["c"],
    }
    tickets=db.execute("""SELECT t.*, e.name estado, p.name prioridad, u.nombre cliente,
                          te.nombre tecnico, c.nombre categoria
                          FROM tickets t
                          JOIN estados_ticket e ON e.id=t.estado_id
                          LEFT JOIN prioridades p ON p.id=t.prioridad_id
                          JOIN usuarios u ON u.id=t.usuario_id
                          LEFT JOIN usuarios te ON te.id=t.tecnico_id
                          LEFT JOIN categorias c ON c.id=t.categoria_id
                          ORDER BY t.created_at DESC LIMIT 8""").fetchall()
    db.close()
    return render_template("admin_dashboard.html",metrics=metrics,tickets=tickets)

@admin_bp.route("/users", methods=["GET","POST"])
@role_required("ADMINISTRADOR")
def users():
    db=get_db()
    if request.method=="POST":
        nombre=request.form["nombre"].strip()
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        role=request.form["role"]
        role_id=db.execute("SELECT id FROM roles WHERE name=?",(role,)).fetchone()["id"]
        try:
            db.execute("INSERT INTO usuarios(nombre,email,password_hash,role_id) VALUES(?,?,?,?)",
                       (nombre,email,generate_password_hash(password),role_id))
            db.commit(); flash("Usuario creado correctamente.","success")
        except Exception:
            flash("No fue posible crear el usuario. Verifica el correo.","danger")
    users=db.execute("""SELECT u.*,r.name role,e.nombre empresa FROM usuarios u
                        JOIN roles r ON r.id=u.role_id LEFT JOIN empresas e ON e.id=u.empresa_id
                        ORDER BY u.id DESC""").fetchall()
    db.close()
    return render_template("users.html",users=users)

@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@role_required("ADMINISTRADOR")
def toggle_user(user_id):
    db=get_db()
    row=db.execute("SELECT estado FROM usuarios WHERE id=?",(user_id,)).fetchone()
    if row:
        new="INACTIVO" if row["estado"]=="ACTIVO" else "ACTIVO"
        db.execute("UPDATE usuarios SET estado=? WHERE id=?",(new,user_id)); db.commit()
    db.close()
    return redirect(url_for("admin.users"))

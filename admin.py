from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
try:
    from .database import get_db
    from .decorators import role_required
except ImportError:
    from database import get_db
    from decorators import role_required

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/")
@admin_bp.route("/dashboard")
@role_required("ADMINISTRADOR")
def dashboard():
    db = get_db()

    total_tickets = db.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"]
    abiertos = db.execute("""SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id=t.estado_id
                             WHERE e.name IN ('NUEVO', 'ASIGNADO', 'PENDIENTE', 'PENDIENTE DEL USUARIO')""").fetchone()["c"]
    en_proceso = db.execute("""SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id=t.estado_id
                               WHERE e.name IN ('EN DIAGNÓSTICO', 'EN PROCESO', 'ESCALADO')""").fetchone()["c"]
    solucionados = db.execute("""SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id=t.estado_id
                                 WHERE e.name IN ('RESUELTO', 'CERRADO')""").fetchone()["c"]
    criticos = db.execute("""SELECT COUNT(*) c FROM tickets t JOIN prioridades p ON p.id=t.prioridad_id
                             WHERE p.name='CRITICA'""").fetchone()["c"]

    total_usuarios = db.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"]
    total_equipos = db.execute("SELECT COUNT(*) c FROM equipos").fetchone()["c"]
    total_empresas = db.execute("SELECT COUNT(*) c FROM empresas").fetchone()["c"]
    total_tecnicos = db.execute("""SELECT COUNT(*) c FROM usuarios u JOIN roles r ON r.id=u.role_id
                                   WHERE r.name LIKE 'TECNICO%'""").fetchone()["c"]

    if total_tickets > 0:
        sla_cumplimiento = f"{round((solucionados / total_tickets) * 100, 1)}%"
    else:
        sla_cumplimiento = "—"

    metrics = {
        "tickets": total_tickets,
        "abiertos": abiertos,
        "en_proceso": en_proceso,
        "solucionados": solucionados,
        "criticos": criticos,
        "proximos_vencer": db.execute("""SELECT COUNT(*) c FROM tickets t JOIN prioridades p ON p.id=t.prioridad_id JOIN estados_ticket e ON e.id=t.estado_id WHERE p.name IN ('CRITICA','ALTA') AND e.name NOT IN ('RESUELTO','CERRADO')""").fetchone()["c"],
        "sla_cumplimiento": sla_cumplimiento,
        "usuarios": total_usuarios,
        "equipos": total_equipos,
        "empresas": total_empresas,
        "tecnicos": total_tecnicos,
        "servicios_activos": 6
    }

    tickets = db.execute("""SELECT t.*, e.name estado, p.name prioridad, u.nombre cliente,
                             te.nombre tecnico, c.nombre categoria
                             FROM tickets t
                             JOIN estados_ticket e ON e.id=t.estado_id
                             LEFT JOIN prioridades p ON p.id=t.prioridad_id
                             JOIN usuarios u ON u.id=t.usuario_id
                             LEFT JOIN usuarios te ON te.id=t.tecnico_id
                             LEFT JOIN categorias c ON c.id=t.categoria_id
                             ORDER BY t.created_at DESC LIMIT 8""").fetchall()

    tickets_por_prioridad = db.execute("""SELECT p.name, COUNT(t.id) total FROM prioridades p
                                          LEFT JOIN tickets t ON t.prioridad_id=p.id
                                          GROUP BY p.name ORDER BY p.nivel DESC""").fetchall()

    tickets_por_estado = db.execute("""SELECT e.name, COUNT(t.id) total FROM estados_ticket e
                                       LEFT JOIN tickets t ON t.estado_id=e.id
                                       GROUP BY e.name""").fetchall()

    actividad_reciente = db.execute("""SELECT h.*, u.nombre, t.titulo FROM historial_tickets h
                                       JOIN usuarios u ON u.id=h.usuario_id
                                       JOIN tickets t ON t.id=h.ticket_id
                                       ORDER BY h.created_at DESC LIMIT 6""").fetchall()

    db.close()
    return render_template("admin_dashboard.html", metrics=metrics, tickets=tickets,
                           tickets_por_prioridad=tickets_por_prioridad,
                           tickets_por_estado=tickets_por_estado,
                           actividad_reciente=actividad_reciente)

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

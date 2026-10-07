from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from .database import get_db
from .decorators import login_required, role_required

tickets_bp = Blueprint("tickets", __name__)

def base_query(extra="", params=()):
    db = get_db()
    q = """SELECT t.*, e.name estado, p.name prioridad, c.nombre categoria, u.nombre cliente,
                 te.nombre tecnico, n.name nivel
          FROM tickets t
          JOIN estados_ticket e ON e.id=t.estado_id
          LEFT JOIN prioridades p ON p.id=t.prioridad_id
          LEFT JOIN categorias c ON c.id=t.categoria_id
          JOIN usuarios u ON u.id=t.usuario_id
          LEFT JOIN usuarios te ON te.id=t.tecnico_id
          LEFT JOIN niveles_soporte n ON n.id=t.nivel_id """ + extra
    rows = db.execute(q, params).fetchall()
    db.close()
    return rows

@tickets_bp.route("/client")
@login_required
def client_dashboard():
    return redirect(url_for("main.inicio"))

@tickets_bp.route("/technician")
@login_required
def technician_dashboard():
    return redirect(url_for("main.inicio"))

@tickets_bp.route("/")
@login_required
def index():
    role = session.get("role", "")
    user_id = session.get("user_id")

    if role == "ADMINISTRADOR":
        tickets = base_query("ORDER BY t.created_at DESC")
    elif role == "SOPORTE TI" or role.startswith("TECNICO"):
        tickets = base_query("WHERE t.tecnico_id=? OR t.tecnico_id IS NULL ORDER BY t.created_at DESC", (user_id,))
    else: # USUARIO / CLIENTE
        tickets = base_query("WHERE t.usuario_id=? ORDER BY t.created_at DESC", (user_id,))

    return render_template("tickets.html", tickets=tickets)

@tickets_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    db = get_db()
    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        cat_nombre = request.form.get("categoria", "")
        prio_nombre = request.form.get("prioridad", "")

        if titulo and descripcion:
            estado = db.execute("SELECT id FROM estados_ticket WHERE name='NUEVO'").fetchone()["id"]
            prioridad = db.execute("SELECT id FROM prioridades WHERE name=?", (prio_nombre,)).fetchone()
            categoria = db.execute("SELECT id FROM categorias WHERE nombre=?", (cat_nombre,)).fetchone()
            nivel = db.execute("SELECT id FROM niveles_soporte WHERE name='NIVEL 1'").fetchone()

            prio_id = prioridad["id"] if prioridad else 1
            cat_id = categoria["id"] if categoria else 1
            niv_id = nivel["id"] if nivel else 1

            cursor = db.execute("""
                INSERT INTO tickets(titulo, descripcion, usuario_id, empresa_id, categoria_id, prioridad_id, estado_id, nivel_id)
                VALUES(?,?,?,?,?,?,?,?)
            """, (titulo, descripcion, session["user_id"], session.get("empresa_id"), cat_id, prio_id, estado, niv_id))

            ticket_id = cursor.lastrowid

            db.execute("INSERT INTO historial_tickets(ticket_id, usuario_id, accion, detalle) VALUES(?,?,?,?)",
                       (ticket_id, session["user_id"], "Creación", "Ticket registrado en la plataforma"))

            db.commit()
            db.close()
            flash("Solicitud creada exitosamente.", "success")
            return redirect(url_for("main.inicio"))

    categories = db.execute("SELECT * FROM categorias").fetchall()
    priorities = db.execute("SELECT * FROM prioridades ORDER BY nivel").fetchall()
    db.close()
    return render_template("ticket_form.html", categories=categories, priorities=priorities)

@tickets_bp.route("/<int:ticket_id>")
@login_required
def detail(ticket_id):
    db = get_db()
    ticket = db.execute("""
        SELECT t.*, e.name estado, p.name prioridad, c.nombre categoria, u.nombre cliente, u.email cliente_email,
               te.nombre tecnico, n.name nivel
        FROM tickets t
        JOIN estados_ticket e ON e.id=t.estado_id
        LEFT JOIN prioridades p ON p.id=t.prioridad_id
        LEFT JOIN categorias c ON c.id=t.categoria_id
        JOIN usuarios u ON u.id=t.usuario_id
        LEFT JOIN usuarios te ON te.id=t.tecnico_id
        LEFT JOIN niveles_soporte n ON n.id=t.nivel_id
        WHERE t.id=?
    """, (ticket_id,)).fetchone()

    if not ticket:
        db.close()
        flash("El ticket solicitado no existe.", "danger")
        return redirect(url_for("tickets.index"))

    # Permission check for ticket details
    role = session.get("role", "")
    user_id = session.get("user_id")
    if role not in ("ADMINISTRADOR", "SOPORTE TI") and not role.startswith("TECNICO"):
        if ticket["usuario_id"] != user_id:
            db.close()
            return render_template("403.html"), 403

    history = db.execute("""
        SELECT h.*, u.nombre
        FROM historial_tickets h
        JOIN usuarios u ON u.id=h.usuario_id
        WHERE h.ticket_id=?
        ORDER BY h.created_at DESC
    """, (ticket_id,)).fetchall()

    diagnostics = db.execute("""
        SELECT d.*, u.nombre
        FROM diagnosticos d
        JOIN usuarios u ON u.id=d.tecnico_id
        WHERE d.ticket_id=?
        ORDER BY d.id DESC
    """, (ticket_id,)).fetchall()

    solutions = db.execute("""
        SELECT s.*, u.nombre
        FROM soluciones s
        JOIN usuarios u ON u.id=s.tecnico_id
        WHERE s.ticket_id=?
        ORDER BY s.id DESC
    """, (ticket_id,)).fetchall()

    tecnicos = db.execute("""
        SELECT u.id, u.nombre
        FROM usuarios u
        JOIN roles r ON r.id=u.role_id
        WHERE r.name IN ('SOPORTE TI','TECNICO_NIVEL_1','TECNICO_NIVEL_2','TECNICO_NIVEL_3','ADMINISTRADOR')
    """).fetchall()

    db.close()
    return render_template("ticket_detail.html", ticket=ticket, history=history, diagnostics=diagnostics, solutions=solutions, tecnicos=tecnicos)

@tickets_bp.route("/<int:ticket_id>/update", methods=["POST"])
@role_required("ADMINISTRADOR", "SOPORTE TI")
def update(ticket_id):
    db = get_db()
    estado_nombre = request.form.get("estado")
    estado = db.execute("SELECT id, name FROM estados_ticket WHERE name=?", (estado_nombre,)).fetchone()
    if estado:
        db.execute("UPDATE tickets SET estado_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (estado["id"], ticket_id))
        db.execute("INSERT INTO historial_tickets(ticket_id, usuario_id, accion, detalle) VALUES(?,?,?,?)",
                   (ticket_id, session["user_id"], "Cambio de estado", f"Estado cambiado a: {estado['name']}"))
        db.commit()
        flash("Estado del ticket actualizado.", "success")
    db.close()
    return redirect(url_for("tickets.detail", ticket_id=ticket_id))

@tickets_bp.route("/<int:ticket_id>/assign", methods=["POST"])
@role_required("ADMINISTRADOR", "SOPORTE TI")
def assign(ticket_id):
    db = get_db()
    tecnico_id = request.form.get("tecnico_id")
    tech = db.execute("SELECT id, nombre FROM usuarios WHERE id=?", (tecnico_id,)).fetchone()
    if tech:
        db.execute("UPDATE tickets SET tecnico_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (tech["id"], ticket_id))
        db.execute("INSERT INTO historial_tickets(ticket_id, usuario_id, accion, detalle) VALUES(?,?,?,?)",
                   (ticket_id, session["user_id"], "Asignación de técnico", f"Asignado a: {tech['nombre']}"))
        db.commit()
        flash(f"Técnico {tech['nombre']} asignado al ticket.", "success")
    db.close()
    return redirect(url_for("tickets.detail", ticket_id=ticket_id))

@tickets_bp.route("/<int:ticket_id>/diagnosis", methods=["POST"])
@role_required("ADMINISTRADOR", "SOPORTE TI")
def diagnosis(ticket_id):
    db = get_db()
    desc = request.form.get("descripcion", "").strip()
    if desc:
        db.execute("INSERT INTO diagnosticos(ticket_id, tecnico_id, descripcion) VALUES(?,?,?)",
                   (ticket_id, session["user_id"], desc))
        db.execute("INSERT INTO historial_tickets(ticket_id, usuario_id, accion, detalle) VALUES(?,?,?,?)",
                   (ticket_id, session["user_id"], "Diagnóstico", "Se registró un nuevo diagnóstico técnico"))
        db.commit()
        flash("Diagnóstico registrado correctamente.", "success")
    db.close()
    return redirect(url_for("tickets.detail", ticket_id=ticket_id))

@tickets_bp.route("/<int:ticket_id>/solution", methods=["POST"])
@role_required("ADMINISTRADOR", "SOPORTE TI")
def solution(ticket_id):
    db = get_db()
    desc = request.form.get("descripcion", "").strip()
    if desc:
        estado_resuelto = db.execute("SELECT id FROM estados_ticket WHERE name='RESUELTO'").fetchone()
        db.execute("INSERT INTO soluciones(ticket_id, tecnico_id, descripcion) VALUES(?,?,?)",
                   (ticket_id, session["user_id"], desc))
        if estado_resuelto:
            db.execute("UPDATE tickets SET estado_id=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (estado_resuelto["id"], ticket_id))
        db.execute("INSERT INTO historial_tickets(ticket_id, usuario_id, accion, detalle) VALUES(?,?,?,?)",
                   (ticket_id, session["user_id"], "Solución y Cierre", "Se registró la solución y el ticket fue resuelto."))
        db.commit()
        flash("Solución registrada y ticket marcado como RESUELTO.", "success")
    db.close()
    return redirect(url_for("tickets.detail", ticket_id=ticket_id))

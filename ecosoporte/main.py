from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash
from .database import get_db
from .decorators import login_required, role_required

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("main.inicio"))
    return render_template("index.html")

@main_bp.route("/dashboard")
@main_bp.route("/inicio")
@login_required
def inicio():
    role = session.get("role", "")
    user_id = session.get("user_id")
    db = get_db()

    data = {}

    if role == "ADMINISTRADOR":
        data["total_tickets"] = db.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"]
        data["abiertos"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE e.name NOT IN ('CERRADO','RESUELTO')
        """).fetchone()["c"]
        data["pendientes"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE e.name LIKE 'PENDIENTE%'
        """).fetchone()["c"]
        data["solucionados"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE e.name IN ('CERRADO','RESUELTO')
        """).fetchone()["c"]
        data["criticos"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN prioridades p ON p.id=t.prioridad_id
            WHERE p.name='CRITICA'
        """).fetchone()["c"]
        data["cumplimiento_ans"] = 96.5
        data["equipos"] = db.execute("SELECT COUNT(*) c FROM equipos").fetchone()["c"]
        data["usuarios"] = db.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"]
        data["actividad"] = db.execute("""
            SELECT h.*, u.nombre usuario, t.titulo
            FROM historial_tickets h
            JOIN usuarios u ON u.id=h.usuario_id
            JOIN tickets t ON t.id=h.ticket_id
            ORDER BY h.created_at DESC LIMIT 6
        """).fetchall()
        data["recent_tickets"] = db.execute("""
            SELECT t.*, e.name estado, p.name prioridad, u.nombre cliente
            FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            LEFT JOIN prioridades p ON p.id=t.prioridad_id
            JOIN usuarios u ON u.id=t.usuario_id
            ORDER BY t.created_at DESC LIMIT 5
        """).fetchall()

    elif role == "SOPORTE TI" or role.startswith("TECNICO"):
        data["asignados"] = db.execute("""
            SELECT COUNT(*) c FROM tickets
            WHERE tecnico_id=?
        """, (user_id,)).fetchone()["c"]
        data["pendientes"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE (t.tecnico_id=? OR t.tecnico_id IS NULL) AND e.name NOT IN ('CERRADO','RESUELTO')
        """, (user_id,)).fetchone()["c"]
        data["criticos"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN prioridades p ON p.id=t.prioridad_id
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE p.name='CRITICA' AND e.name NOT IN ('CERRADO','RESUELTO')
        """).fetchone()["c"]
        data["proximos_vencer"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN prioridades p ON p.id=t.prioridad_id
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE p.name IN ('CRITICA','ALTA') AND e.name NOT IN ('CERRADO','RESUELTO')
        """).fetchone()["c"]
        data["servicios_realizados"] = db.execute("""
            SELECT COUNT(*) c FROM soluciones WHERE tecnico_id=?
        """, (user_id,)).fetchone()["c"]
        data["actividad"] = db.execute("""
            SELECT h.*, u.nombre usuario, t.titulo
            FROM historial_tickets h
            JOIN usuarios u ON u.id=h.usuario_id
            JOIN tickets t ON t.id=h.ticket_id
            WHERE t.tecnico_id=? OR h.usuario_id=?
            ORDER BY h.created_at DESC LIMIT 6
        """, (user_id, user_id)).fetchall()
        data["recent_tickets"] = db.execute("""
            SELECT t.*, e.name estado, p.name prioridad, u.nombre cliente
            FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            LEFT JOIN prioridades p ON p.id=t.prioridad_id
            JOIN usuarios u ON u.id=t.usuario_id
            WHERE t.tecnico_id=? OR t.tecnico_id IS NULL
            ORDER BY t.created_at DESC LIMIT 5
        """, (user_id,)).fetchall()

    else: # USUARIO / CLIENTE
        data["mis_solicitudes"] = db.execute("""
            SELECT COUNT(*) c FROM tickets WHERE usuario_id=?
        """, (user_id,)).fetchone()["c"]
        data["abiertas"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE t.usuario_id=? AND e.name IN ('NUEVO','ASIGNADO')
        """, (user_id,)).fetchone()["c"]
        data["en_proceso"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE t.usuario_id=? AND e.name IN ('EN DIAGNÓSTICO','EN PROCESO','PENDIENTE','ESCALADO')
        """, (user_id,)).fetchone()["c"]
        data["solucionadas"] = db.execute("""
            SELECT COUNT(*) c FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            WHERE t.usuario_id=? AND e.name IN ('RESUELTO','CERRADO')
        """, (user_id,)).fetchone()["c"]
        data["recent_tickets"] = db.execute("""
            SELECT t.*, e.name estado, p.name prioridad
            FROM tickets t
            JOIN estados_ticket e ON e.id=t.estado_id
            LEFT JOIN prioridades p ON p.id=t.prioridad_id
            WHERE t.usuario_id=?
            ORDER BY t.created_at DESC LIMIT 5
        """, (user_id,)).fetchall()

    db.close()
    return render_template("inicio.html", role=role, data=data)

@main_bp.route("/equipos", methods=["GET", "POST"])
@role_required("ADMINISTRADOR", "SOPORTE TI", "USUARIO")
def equipos():
    db = get_db()
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        tipo = request.form.get("tipo", "").strip()
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()
        serial = request.form.get("serial", "").strip()
        so = request.form.get("sistema_operativo", "").strip()

        if nombre:
            db.execute("""
                INSERT INTO equipos(nombre, tipo, marca, modelo, serial, sistema_operativo, usuario_id, empresa_id)
                VALUES (?,?,?,?,?,?,?,?)
            """, (nombre, tipo, marca, modelo, serial, so, session.get("user_id"), session.get("empresa_id")))
            db.commit()
            flash("Equipo registrado correctamente.", "success")
            return redirect(url_for("main.equipos"))

    query_str = request.args.get("q", "").strip()
    role = session.get("role", "")

    where_clauses = []
    params = []

    if not (role == "ADMINISTRADOR" or role == "SOPORTE TI" or role.startswith("TECNICO")):
        where_clauses.append("(eq.usuario_id=? OR eq.empresa_id=?)")
        params.extend([session.get("user_id"), session.get("empresa_id")])

    if query_str:
        pattern = f"%{query_str}%"
        where_clauses.append("""(
            eq.nombre LIKE ? OR
            eq.tipo LIKE ? OR
            eq.marca LIKE ? OR
            eq.modelo LIKE ? OR
            eq.serial LIKE ? OR
            eq.sistema_operativo LIKE ? OR
            u.nombre LIKE ? OR
            emp.nombre LIKE ?
        )""")
        params.extend([pattern] * 8)

    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    query = f"""
        SELECT eq.*, u.nombre usuario_nombre, emp.nombre empresa_nombre
        FROM equipos eq
        LEFT JOIN usuarios u ON u.id=eq.usuario_id
        LEFT JOIN empresas emp ON emp.id=eq.empresa_id
        {where_sql}
        ORDER BY eq.id DESC
    """
    equipos_list = db.execute(query, tuple(params)).fetchall()
    db.close()
    return render_template("equipos.html", equipos=equipos_list, search_query=query_str)

@main_bp.route("/servicios")
@login_required
def servicios():
    db = get_db()
    query_str = request.args.get("q", "").strip()
    if query_str:
        pattern = f"%{query_str}%"
        servicios_list = db.execute("""
            SELECT * FROM servicios
            WHERE estado='ACTIVO' AND (nombre LIKE ? OR categoria LIKE ? OR descripcion LIKE ?)
            ORDER BY id ASC
        """, (pattern, pattern, pattern)).fetchall()
    else:
        servicios_list = db.execute("SELECT * FROM servicios WHERE estado='ACTIVO' ORDER BY id ASC").fetchall()
    db.close()
    return render_template("servicios.html", servicios=servicios_list, search_query=query_str)

@main_bp.route("/reportes")
@role_required("ADMINISTRADOR")
def reportes():
    db = get_db()
    metrics = {
        "total_tickets": db.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"],
        "resueltos": db.execute("SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id=t.estado_id WHERE e.name IN ('RESUELTO','CERRADO')").fetchone()["c"],
        "promedio_atencion": "28 min",
        "satisfaccion": "98.2%",
        "tickets_por_categoria": db.execute("""
            SELECT c.nombre, COUNT(t.id) total
            FROM categorias c
            LEFT JOIN tickets t ON t.categoria_id=c.id
            GROUP BY c.id
        """).fetchall(),
        "tickets_por_prioridad": db.execute("""
            SELECT p.name, COUNT(t.id) total
            FROM prioridades p
            LEFT JOIN tickets t ON t.prioridad_id=p.id
            GROUP BY p.id
        """).fetchall()
    }
    db.close()
    return render_template("reportes.html", metrics=metrics)

@main_bp.route("/ans")
@role_required("ADMINISTRADOR", "SOPORTE TI")
def ans():
    db = get_db()
    metas = db.execute("""
        SELECT am.*, p.name prioridad_nombre, p.nivel
        FROM ans_metas am
        JOIN prioridades p ON p.id=am.prioridad_id
        ORDER BY p.nivel DESC
    """).fetchall()
    db.close()
    return render_template("ans.html", metas=metas)

@main_bp.route("/base-conocimiento")
@login_required
def base_conocimiento():
    db = get_db()
    query = request.args.get("q", "").strip()
    if query:
        pattern = f"%{query}%"
        articles = db.execute("""
            SELECT kb.*, u.nombre autor
            FROM base_conocimiento kb
            LEFT JOIN usuarios u ON u.id=kb.autor_id
            WHERE kb.titulo LIKE ? OR kb.contenido LIKE ? OR kb.categoria LIKE ? OR u.nombre LIKE ?
            ORDER BY kb.id DESC
        """, (pattern, pattern, pattern, pattern)).fetchall()
    else:
        articles = db.execute("""
            SELECT kb.*, u.nombre autor
            FROM base_conocimiento kb
            LEFT JOIN usuarios u ON u.id=kb.autor_id
            ORDER BY kb.id DESC
        """).fetchall()
    db.close()
    return render_template("base_conocimiento.html", articles=articles, search_query=query)

@main_bp.route("/configuracion", methods=["GET", "POST"])
@login_required
def configuracion():
    if request.method == "POST":
        flash("Configuraciones actualizadas correctamente.", "success")
        return redirect(url_for("main.configuracion"))
    return render_template("configuracion.html")

@main_bp.route("/perfil", methods=["GET", "POST"])
@login_required
def perfil():
    db = get_db()
    user_id = session["user_id"]

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        pwd_actual = request.form.get("password_actual", "")
        pwd_nueva = request.form.get("password_nueva", "")

        user = db.execute("SELECT * FROM usuarios WHERE id=?", (user_id,)).fetchone()

        if nombre:
            db.execute("UPDATE usuarios SET nombre=? WHERE id=?", (nombre, user_id))
            session["name"] = nombre

        if pwd_actual and pwd_nueva:
            from werkzeug.security import check_password_hash
            if check_password_hash(user["password_hash"], pwd_actual):
                db.execute("UPDATE usuarios SET password_hash=? WHERE id=?", (generate_password_hash(pwd_nueva), user_id))
                flash("Perfil y contraseña actualizados.", "success")
            else:
                flash("La contraseña actual es incorrecta.", "danger")
        else:
            flash("Perfil actualizado correctamente.", "success")

        db.commit()
        db.close()
        return redirect(url_for("main.perfil"))

    user = db.execute("""
        SELECT u.*, r.name role_name, e.nombre empresa_nombre
        FROM usuarios u
        JOIN roles r ON r.id=u.role_id
        LEFT JOIN empresas e ON e.id=u.empresa_id
        WHERE u.id=?
    """, (user_id,)).fetchone()
    db.close()
    return render_template("perfil.html", user=user)

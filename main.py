from flask import Blueprint, render_template, session, redirect, url_for, request, flash
try:
    from .database import get_db
    from .decorators import login_required, role_required
except ImportError:
    from database import get_db
    from decorators import login_required, role_required

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
    if role and role.startswith("TECNICO"):
        return redirect(url_for("main.soporte_ti"))
    return redirect(url_for("tickets.client_dashboard"))

@main_bp.route("/soporte-ti")
@role_required("ADMINISTRADOR", "TECNICO_NIVEL_1", "TECNICO_NIVEL_2", "TECNICO_NIVEL_3")
def soporte_ti():
    db = get_db()
    prioridad = request.args.get("prioridad", "")
    estado = request.args.get("estado", "")
    tecnico = request.args.get("tecnico", "")

    query = """SELECT t.*, e.name estado, p.name prioridad, c.nombre categoria, u.nombre cliente,
                      te.nombre tecnico, n.name nivel
               FROM tickets t
               JOIN estados_ticket e ON e.id = t.estado_id
               LEFT JOIN prioridades p ON p.id = t.prioridad_id
               LEFT JOIN categorias c ON c.id = t.categoria_id
               JOIN usuarios u ON u.id = t.usuario_id
               LEFT JOIN usuarios te ON te.id = t.tecnico_id
               LEFT JOIN niveles_soporte n ON n.id = t.nivel_id
               WHERE 1=1"""
    params = []
    if prioridad:
        query += " AND p.name = ?"
        params.append(prioridad)
    if estado:
        query += " AND e.name = ?"
        params.append(estado)
    if tecnico:
        query += " AND te.nombre LIKE ?"
        params.append(f"%{tecnico}%")

    query += " ORDER BY t.created_at DESC"
    tickets = db.execute(query, params).fetchall()

    tecnicos = db.execute("""SELECT u.*, r.name role FROM usuarios u
                            JOIN roles r ON r.id = u.role_id
                            WHERE r.name LIKE 'TECNICO%' AND u.estado = 'ACTIVO'""").fetchall()

    metrics = {
        "asignados": db.execute("SELECT COUNT(*) c FROM tickets WHERE tecnico_id = ?", (session["user_id"],)).fetchone()["c"] if session.get("role") != "ADMINISTRADOR" else db.execute("SELECT COUNT(*) c FROM tickets WHERE tecnico_id IS NOT NULL").fetchone()["c"],
        "pendientes": db.execute("SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id = t.estado_id WHERE e.name IN ('NUEVO', 'PENDIENTE', 'PENDIENTE DEL USUARIO')").fetchone()["c"],
        "en_proceso": db.execute("SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id = t.estado_id WHERE e.name IN ('ASIGNADO', 'EN DIAGNÓSTICO', 'EN PROCESO')").fetchone()["c"],
        "criticos": db.execute("SELECT COUNT(*) c FROM tickets t JOIN prioridades p ON p.id = t.prioridad_id WHERE p.name = 'CRITICA'").fetchone()["c"],
        "solucionados": db.execute("SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id = t.estado_id WHERE e.name IN ('RESUELTO', 'CERRADO')").fetchone()["c"],
    }

    equipos_count = db.execute("SELECT COUNT(*) c FROM equipos").fetchone()["c"]
    db.close()
    return render_template("soporte_ti.html", tickets=tickets, tecnicos=tecnicos, metrics=metrics, equipos_count=equipos_count)

@main_bp.route("/equipos", methods=["GET", "POST"])
@login_required
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
            db.execute("""INSERT INTO equipos(nombre, tipo, marca, modelo, serial, sistema_operativo, usuario_id, empresa_id)
                          VALUES(?, ?, ?, ?, ?, ?, ?, ?)""",
                       (nombre, tipo, marca, modelo, serial, so, session.get("user_id"), session.get("empresa_id")))
            db.commit()
            flash("Equipo registrado exitosamente.", "success")
        db.close()
        return redirect(url_for("main.equipos"))

    if session.get("role") == "ADMINISTRADOR" or session.get("role", "").startswith("TECNICO"):
        equipos = db.execute("""SELECT eq.*, u.nombre usuario, em.nombre empresa
                                FROM equipos eq
                                LEFT JOIN usuarios u ON u.id = eq.usuario_id
                                LEFT JOIN empresas em ON em.id = eq.empresa_id
                                ORDER BY eq.id DESC""").fetchall()
    else:
        equipos = db.execute("""SELECT eq.*, u.nombre usuario, em.nombre empresa
                                FROM equipos eq
                                LEFT JOIN usuarios u ON u.id = eq.usuario_id
                                LEFT JOIN empresas em ON em.id = eq.empresa_id
                                WHERE eq.usuario_id = ? OR eq.empresa_id = ?
                                ORDER BY eq.id DESC""", (session.get("user_id"), session.get("empresa_id"))).fetchall()
    db.close()
    return render_template("equipos.html", equipos=equipos)

@main_bp.route("/servicios")
@login_required
def servicios():
    servicios_lista = [
        {"id": 1, "nombre": "Soporte Técnico Especializado", "categoria": "Mesa de Ayuda", "descripcion": "Atención rápida y resolución de incidencias informáticas para usuarios y empresas.", "icono": "🛠️", "estado": "ACTIVO", "sla": "Respuesta < 1 hora"},
        {"id": 2, "nombre": "Mantenimiento Preventivo y Correctivo", "categoria": "Hardware & Equipos", "descripcion": "Limpieza, optimización de hardware, reemplazo de piezas y diagnósticos técnicos.", "icono": "💻", "estado": "ACTIVO", "sla": "Atención programada"},
        {"id": 3, "nombre": "Administración de Redes y Conectividad", "categoria": "Infraestructura", "descripcion": "Monitoreo de routers, switches, VPN empresarial y seguridad en red interna.", "icono": "🌐", "estado": "ACTIVO", "sla": "24/7 Monitoreo"},
        {"id": 4, "nombre": "Gestión de Servidores y Nube", "categoria": "Sistemas", "descripcion": "Configuración de backups, servidores de archivos y servicios en la nube.", "icono": "☁️", "estado": "ACTIVO", "sla": "99.9% Disponibilidad"},
        {"id": 5, "nombre": "Ciberseguridad y Protección de Datos", "categoria": "Seguridad", "descripcion": "Antivirus corporativo, auditorías de seguridad, firewall e higiene digital.", "icono": "🔒", "estado": "ACTIVO", "sla": "Respuesta inmediata"},
        {"id": 6, "nombre": "Reutilización y Tecnología Sostenible", "categoria": "EcoSoporte", "descripcion": "Reparación, repotenciación de equipos y reciclaje electrónico responsable.", "icono": "♻️", "estado": "ACTIVO", "sla": "Evaluación continua"}
    ]
    return render_template("servicios.html", servicios=servicios_lista)

@main_bp.route("/reportes")
@role_required("ADMINISTRADOR", "TECNICO_NIVEL_1", "TECNICO_NIVEL_2", "TECNICO_NIVEL_3")
def reportes():
    db = get_db()
    total_tickets = db.execute("SELECT COUNT(*) c FROM tickets").fetchone()["c"]
    resueltos = db.execute("SELECT COUNT(*) c FROM tickets t JOIN estados_ticket e ON e.id = t.estado_id WHERE e.name IN ('RESUELTO', 'CERRADO')").fetchone()["c"]
    por_categoria = db.execute("""SELECT c.nombre, COUNT(t.id) total FROM tickets t
                                  JOIN categorias c ON c.id = t.categoria_id
                                  GROUP BY c.nombre""").fetchall()
    por_prioridad = db.execute("""SELECT p.name, COUNT(t.id) total FROM tickets t
                                  JOIN prioridades p ON p.id = t.prioridad_id
                                  GROUP BY p.name""").fetchall()
    db.close()
    return render_template("reportes.html", total_tickets=total_tickets, resueltos=resueltos, por_categoria=por_categoria, por_prioridad=por_prioridad)

@main_bp.route("/ans-sla")
@login_required
def ans_sla():
    sla_levels = [
        {"prioridad": "CRÍTICA", "tiempo_respuesta": "15 min", "tiempo_solucion": "2 horas", "cumplimiento": "98.5%", "badge": "danger"},
        {"prioridad": "ALTA", "tiempo_respuesta": "30 min", "tiempo_solucion": "4 horas", "cumplimiento": "96.2%", "badge": "warning"},
        {"prioridad": "MEDIA", "tiempo_respuesta": "1 hora", "tiempo_solucion": "8 horas", "cumplimiento": "99.1%", "badge": "info"},
        {"prioridad": "BAJA", "tiempo_respuesta": "2 horas", "tiempo_solucion": "24 horas", "cumplimiento": "99.8%", "badge": "success"}
    ]
    return render_template("ans_sla.html", sla_levels=sla_levels)

@main_bp.route("/base-conocimiento")
@login_required
def base_conocimiento():
    articulos = [
        {"id": 1, "titulo": "¿Cómo solicitar soporte técnico correctamente?", "categoria": "General", "extracto": "Aprende a detallar tu problema para recibir una atención rápida de nuestros técnicos.", "icono": "📝"},
        {"id": 2, "titulo": "Solución a problemas comunes de conectividad Wi-Fi", "categoria": "Redes", "extracto": "Pasos para reiniciar interfaces de red y comprobar DNS o dirección IP.", "icono": "📶"},
        {"id": 3, "titulo": "Buenas prácticas de ciberseguridad y gestión de contraseñas", "categoria": "Seguridad", "extracto": "Recomendaciones para proteger tu cuenta y evitar intentos de phishing.", "icono": "🛡️"},
        {"id": 4, "titulo": "Mantenimiento sostenible para alargar la vida de tu equipo", "categoria": "EcoSoporte", "extracto": "Guía práctica para optimizar batería, temperatura y almacenamiento.", "icono": "🌱"}
    ]
    return render_template("base_conocimiento.html", articulos=articulos)

@main_bp.route("/configuracion")
@login_required
def configuracion():
    db = get_db()
    usuario = db.execute("""SELECT u.*, r.name role, e.nombre empresa FROM usuarios u
                            JOIN roles r ON r.id = u.role_id
                            LEFT JOIN empresas e ON e.id = u.empresa_id
                            WHERE u.id = ?""", (session.get("user_id"),)).fetchone()
    db.close()
    return render_template("configuracion.html", usuario=usuario)

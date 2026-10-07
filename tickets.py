from flask import Blueprint, render_template, request, redirect, url_for, session, flash
try:
    from .database import get_db
    from .decorators import login_required, role_required
except ImportError:
    from database import get_db
    from decorators import login_required, role_required

tickets_bp=Blueprint("tickets",__name__)

def base_query(extra="", params=()):
    db=get_db()
    q="""SELECT t.*, e.name estado,p.name prioridad,c.nombre categoria,u.nombre cliente,
                 te.nombre tecnico, n.name nivel
          FROM tickets t JOIN estados_ticket e ON e.id=t.estado_id
          LEFT JOIN prioridades p ON p.id=t.prioridad_id
          LEFT JOIN categorias c ON c.id=t.categoria_id
          JOIN usuarios u ON u.id=t.usuario_id
          LEFT JOIN usuarios te ON te.id=t.tecnico_id
          LEFT JOIN niveles_soporte n ON n.id=t.nivel_id """+extra
    rows=db.execute(q,params).fetchall(); db.close(); return rows

@tickets_bp.route("/client")
@role_required("CLIENTE")
def client_dashboard():
    db=get_db()
    tickets=base_query("WHERE t.usuario_id=? ORDER BY t.created_at DESC",(session["user_id"],))
    counts={
        "total": len(tickets),
        "abiertos": sum(x["estado"] in ("NUEVO", "ASIGNADO", "PENDIENTE", "PENDIENTE DEL USUARIO") for x in tickets),
        "en_proceso": sum(x["estado"] in ("EN DIAGNÓSTICO", "EN PROCESO", "ESCALADO") for x in tickets),
        "solucionados": sum(x["estado"] in ("RESUELTO", "CERRADO") for x in tickets)
    }
    db.close()
    return render_template("client_dashboard.html",tickets=tickets,counts=counts)

@tickets_bp.route("/technician")
@role_required("TECNICO_NIVEL_1","TECNICO_NIVEL_2","TECNICO_NIVEL_3")
def technician_dashboard():
    db=get_db()
    tickets=base_query("WHERE t.tecnico_id=? OR t.tecnico_id IS NULL ORDER BY t.created_at DESC",(session["user_id"],))
    metrics={
        "asignados": len([t for t in tickets if t["tecnico_id"] == session["user_id"]]),
        "pendientes": len([t for t in tickets if t["estado"] in ('NUEVO', 'PENDIENTE', 'PENDIENTE DEL USUARIO')]),
        "en_proceso": len([t for t in tickets if t["estado"] in ('ASIGNADO', 'EN DIAGNÓSTICO', 'EN PROCESO')]),
        "criticos": len([t for t in tickets if t["prioridad"] == 'CRITICA']),
        "solucionados": len([t for t in tickets if t["estado"] in ('RESUELTO', 'CERRADO')])
    }
    db.close()
    return render_template("technician_dashboard.html",tickets=tickets,metrics=metrics)

@tickets_bp.route("/")
@role_required("ADMINISTRADOR","TECNICO_NIVEL_1","TECNICO_NIVEL_2","TECNICO_NIVEL_3")
def index():
    tickets=base_query("ORDER BY t.created_at DESC")
    return render_template("tickets.html",tickets=tickets)

@tickets_bp.route("/new",methods=["GET","POST"])
@role_required("CLIENTE")
def new():
    db=get_db()
    if request.method=="POST":
        estado=db.execute("SELECT id FROM estados_ticket WHERE name='NUEVO'").fetchone()["id"]
        prioridad=db.execute("SELECT id FROM prioridades WHERE name=?",(request.form["prioridad"],)).fetchone()["id"]
        categoria=db.execute("SELECT id FROM categorias WHERE nombre=?",(request.form["categoria"],)).fetchone()["id"]
        nivel=db.execute("SELECT id FROM niveles_soporte WHERE name='NIVEL 1'").fetchone()["id"]
        db.execute("""INSERT INTO tickets(titulo,descripcion,usuario_id,empresa_id,categoria_id,prioridad_id,estado_id,nivel_id)
                      VALUES(?,?,?,?,?,?,?,?)""",
                   (request.form["titulo"],request.form["descripcion"],session["user_id"],session.get("empresa_id"),
                    categoria,prioridad,estado,nivel))
        db.commit(); db.close(); flash("Ticket creado correctamente.","success")
        return redirect(url_for("tickets.client_dashboard"))
    categories=db.execute("SELECT * FROM categorias").fetchall()
    priorities=db.execute("SELECT * FROM prioridades ORDER BY nivel").fetchall()
    db.close()
    return render_template("ticket_form.html",categories=categories,priorities=priorities)

@tickets_bp.route("/<int:ticket_id>")
@login_required
def detail(ticket_id):
    db=get_db()
    ticket=db.execute("""SELECT t.*,e.name estado,p.name prioridad,c.nombre categoria,u.nombre cliente,
                         te.nombre tecnico,n.name nivel FROM tickets t JOIN estados_ticket e ON e.id=t.estado_id
                         LEFT JOIN prioridades p ON p.id=t.prioridad_id LEFT JOIN categorias c ON c.id=t.categoria_id
                         JOIN usuarios u ON u.id=t.usuario_id LEFT JOIN usuarios te ON te.id=t.tecnico_id
                         LEFT JOIN niveles_soporte n ON n.id=t.nivel_id WHERE t.id=?""",(ticket_id,)).fetchone()
    history=db.execute("""SELECT h.*,u.nombre FROM historial_tickets h JOIN usuarios u ON u.id=h.usuario_id
                          WHERE h.ticket_id=? ORDER BY h.created_at DESC""",(ticket_id,)).fetchall()
    diagnostics=db.execute("SELECT d.*,u.nombre FROM diagnosticos d JOIN usuarios u ON u.id=d.tecnico_id WHERE d.ticket_id=? ORDER BY d.id DESC",(ticket_id,)).fetchall()
    solutions=db.execute("SELECT s.*,u.nombre FROM soluciones s JOIN usuarios u ON u.id=s.tecnico_id WHERE s.ticket_id=? ORDER BY s.id DESC",(ticket_id,)).fetchall()
    db.close()
    if not ticket: return "Ticket no encontrado",404
    return render_template("ticket_detail.html",ticket=ticket,history=history,diagnostics=diagnostics,solutions=solutions)

@tickets_bp.route("/<int:ticket_id>/update",methods=["POST"])
@role_required("ADMINISTRADOR","TECNICO_NIVEL_1","TECNICO_NIVEL_2","TECNICO_NIVEL_3")
def update(ticket_id):
    db=get_db()
    estado=db.execute("SELECT id,name FROM estados_ticket WHERE name=?",(request.form["estado"],)).fetchone()
    if not estado: return redirect(url_for("tickets.detail",ticket_id=ticket_id))
    db.execute("UPDATE tickets SET estado_id=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",(estado["id"],ticket_id))
    db.execute("INSERT INTO historial_tickets(ticket_id,usuario_id,accion,detalle) VALUES(?,?,?,?)",
               (ticket_id,session["user_id"],"Cambio de estado",estado["name"]))
    db.commit(); db.close()
    flash("Ticket actualizado.","success")
    return redirect(url_for("tickets.detail",ticket_id=ticket_id))

@tickets_bp.route("/<int:ticket_id>/assign",methods=["POST"])
@role_required("ADMINISTRADOR")
def assign(ticket_id):
    db=get_db()
    tech=db.execute("SELECT id FROM usuarios WHERE id=?",(request.form["tecnico_id"],)).fetchone()
    if tech:
        db.execute("UPDATE tickets SET tecnico_id=? WHERE id=?",(tech["id"],ticket_id))
        db.execute("INSERT INTO historial_tickets(ticket_id,usuario_id,accion,detalle) VALUES(?,?,?,?)",
                   (ticket_id,session["user_id"],"Asignación","Técnico asignado"))
        db.commit()
    db.close()
    return redirect(url_for("tickets.detail",ticket_id=ticket_id))

@tickets_bp.route("/<int:ticket_id>/diagnosis",methods=["POST"])
@role_required("TECNICO_NIVEL_1","TECNICO_NIVEL_2","TECNICO_NIVEL_3")
def diagnosis(ticket_id):
    db=get_db()
    db.execute("INSERT INTO diagnosticos(ticket_id,tecnico_id,descripcion) VALUES(?,?,?)",(ticket_id,session["user_id"],request.form["descripcion"]))
    db.execute("INSERT INTO historial_tickets(ticket_id,usuario_id,accion,detalle) VALUES(?,?,?,?)",(ticket_id,session["user_id"],"Diagnóstico","Se registró un diagnóstico"))
    db.commit(); db.close()
    return redirect(url_for("tickets.detail",ticket_id=ticket_id))

@tickets_bp.route("/<int:ticket_id>/solution",methods=["POST"])
@role_required("TECNICO_NIVEL_1","TECNICO_NIVEL_2","TECNICO_NIVEL_3")
def solution(ticket_id):
    db=get_db()
    db.execute("INSERT INTO soluciones(ticket_id,tecnico_id,descripcion) VALUES(?,?,?)",(ticket_id,session["user_id"],request.form["descripcion"]))
    db.execute("INSERT INTO historial_tickets(ticket_id,usuario_id,accion,detalle) VALUES(?,?,?,?)",(ticket_id,session["user_id"],"Solución","Se registró una solución"))
    db.commit(); db.close()
    return redirect(url_for("tickets.detail",ticket_id=ticket_id))

from flask import Blueprint, render_template, request, redirect, url_for, flash
from .database import get_db
from .decorators import role_required, login_required

companies_bp = Blueprint("companies", __name__)

@companies_bp.route("/")
@role_required("ADMINISTRADOR", "TECNICO_NIVEL_1", "TECNICO_NIVEL_2", "TECNICO_NIVEL_3")
def index():
    db = get_db()
    query_str = request.args.get("q", "").strip()
    if query_str:
        pattern = f"%{query_str}%"
        companies = db.execute("""
            SELECT * FROM empresas
            WHERE nombre LIKE ? OR nit LIKE ? OR sector LIKE ? OR ciudad LIKE ? OR email LIKE ? OR telefono LIKE ? OR contacto_nombre LIKE ?
            ORDER BY id DESC
        """, (pattern, pattern, pattern, pattern, pattern, pattern, pattern)).fetchall()
    else:
        companies = db.execute("SELECT * FROM empresas ORDER BY id DESC").fetchall()
    db.close()
    return render_template("companies.html", companies=companies, search_query=query_str)

@companies_bp.route("/new", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def new():
    if request.method == "POST":
        data = {k: request.form.get(k, "").strip() for k in request.form.keys()}
        db = get_db()
        db.execute("""INSERT INTO empresas
        (nombre,nit,tipo,sector,email,telefono,sitio_web,departamento,ciudad,localidad,direccion,barrio,
         codigo_postal,contacto_nombre,contacto_cargo,contacto_telefono,contacto_email,medio_contacto,
         horario_atencion,horario_soporte,empleados,equipos_aprox,infraestructura,servidor,red_interna,wifi,nube,sistemas,observaciones)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        tuple(data.get(k, "") for k in ["nombre","nit","tipo","sector","email","telefono","sitio_web","departamento","ciudad","localidad",
        "direccion","barrio","codigo_postal","contacto_nombre","contacto_cargo","contacto_telefono","contacto_email","medio_contacto",
        "horario_atencion","horario_soporte","empleados","equipos_aprox","infraestructura","servidor","red_interna","wifi","nube","sistemas","observaciones"]))
        db.commit()
        db.close()
        flash("Empresa registrada.", "success")
        return redirect(url_for("companies.index"))
    return render_template("company_form.html")

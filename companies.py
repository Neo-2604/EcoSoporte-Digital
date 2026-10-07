from flask import Blueprint, render_template, request, redirect, url_for, flash
try:
    from .database import get_db
    from .decorators import role_required
except ImportError:
    from database import get_db
    from decorators import role_required

companies_bp = Blueprint("companies", __name__)

@companies_bp.route("/")
@role_required("ADMINISTRADOR", "TECNICO_NIVEL_1", "TECNICO_NIVEL_2", "TECNICO_NIVEL_3")
def index():
    db = get_db()
    empresas = db.execute("SELECT * FROM empresas ORDER BY id DESC").fetchall()
    db.close()
    return render_template("companies.html", empresas=empresas)

@companies_bp.route("/new", methods=["GET", "POST"])
@role_required("ADMINISTRADOR")
def new():
    if request.method == "POST":
        db = get_db()
        db.execute("""INSERT INTO empresas(nombre, nit, tipo, sector, email, telefono, contacto_nombre)
                      VALUES(?, ?, ?, ?, ?, ?, ?)""",
                   (request.form.get("nombre"), request.form.get("nit"), request.form.get("tipo"),
                    request.form.get("sector"), request.form.get("email"), request.form.get("telefono"),
                    request.form.get("contacto_nombre")))
        db.commit()
        db.close()
        flash("Empresa registrada correctamente.", "success")
        return redirect(url_for("companies.index"))
    return render_template("company_form.html")

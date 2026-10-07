from functools import wraps
from flask import session, redirect, url_for, render_template

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("auth.login"))

            user_role = session.get("role", "")

            # Map legacy technician roles to SOPORTE TI if checked
            allowed_roles = set(roles)
            if "SOPORTE TI" in allowed_roles:
                allowed_roles.update({"TECNICO_NIVEL_1", "TECNICO_NIVEL_2", "TECNICO_NIVEL_3"})
            if any(r.startswith("TECNICO") for r in roles):
                allowed_roles.add("SOPORTE TI")
            if "USUARIO" in allowed_roles:
                allowed_roles.add("CLIENTE")
            if "CLIENTE" in allowed_roles:
                allowed_roles.add("USUARIO")

            if user_role not in allowed_roles:
                return render_template("403.html"), 403

            return view(*args, **kwargs)
        return wrapped
    return decorator

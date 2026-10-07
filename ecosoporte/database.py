import os, sqlite3
from flask import current_app
from werkzeug.security import generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS empresas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    nit TEXT,
    tipo TEXT,
    sector TEXT,
    email TEXT,
    telefono TEXT,
    sitio_web TEXT,
    pais TEXT DEFAULT 'Colombia',
    departamento TEXT,
    ciudad TEXT,
    localidad TEXT,
    direccion TEXT,
    barrio TEXT,
    codigo_postal TEXT,
    contacto_nombre TEXT,
    contacto_cargo TEXT,
    contacto_telefono TEXT,
    contacto_email TEXT,
    medio_contacto TEXT,
    horario_atencion TEXT,
    horario_soporte TEXT,
    empleados INTEGER,
    equipos_aprox INTEGER,
    infraestructura TEXT,
    servidor TEXT,
    red_interna TEXT,
    wifi TEXT,
    nube TEXT,
    sistemas TEXT,
    observaciones TEXT,
    estado TEXT DEFAULT 'ACTIVA',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    empresa_id INTEGER,
    estado TEXT DEFAULT 'ACTIVO',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(role_id) REFERENCES roles(id),
    FOREIGN KEY(empresa_id) REFERENCES empresas(id)
);
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS prioridades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL,
    nivel INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS estados_ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS niveles_soporte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL,
    name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    usuario_id INTEGER NOT NULL,
    empresa_id INTEGER,
    tecnico_id INTEGER,
    categoria_id INTEGER,
    prioridad_id INTEGER,
    estado_id INTEGER NOT NULL,
    nivel_id INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY(empresa_id) REFERENCES empresas(id),
    FOREIGN KEY(tecnico_id) REFERENCES usuarios(id),
    FOREIGN KEY(categoria_id) REFERENCES categorias(id),
    FOREIGN KEY(prioridad_id) REFERENCES prioridades(id),
    FOREIGN KEY(estado_id) REFERENCES estados_ticket(id),
    FOREIGN KEY(nivel_id) REFERENCES niveles_soporte(id)
);
CREATE TABLE IF NOT EXISTS diagnosticos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    tecnico_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id),
    FOREIGN KEY(tecnico_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS soluciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    tecnico_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id),
    FOREIGN KEY(tecnico_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS historial_tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    accion TEXT NOT NULL,
    detalle TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(ticket_id) REFERENCES tickets(id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER,
    usuario_id INTEGER,
    nombre TEXT NOT NULL,
    tipo TEXT,
    marca TEXT,
    modelo TEXT,
    serial TEXT,
    sistema_operativo TEXT,
    estado TEXT DEFAULT 'ACTIVO',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(empresa_id) REFERENCES empresas(id),
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS mantenimientos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipo_id INTEGER NOT NULL,
    tecnico_id INTEGER,
    tipo TEXT NOT NULL,
    descripcion TEXT,
    fecha TEXT,
    estado TEXT DEFAULT 'PROGRAMADO',
    FOREIGN KEY(equipo_id) REFERENCES equipos(id),
    FOREIGN KEY(tecnico_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS evaluaciones_empresa (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    empresa_id INTEGER NOT NULL,
    tecnico_id INTEGER NOT NULL,
    facilidad_atencion INTEGER NOT NULL,
    disponibilidad_contacto INTEGER NOT NULL,
    condiciones_trabajo INTEGER NOT NULL,
    organizacion_infraestructura INTEGER NOT NULL,
    cumplimiento_recomendaciones INTEGER NOT NULL,
    trato_colaboracion INTEGER NOT NULL,
    condiciones_soporte INTEGER NOT NULL,
    observaciones TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(empresa_id) REFERENCES empresas(id),
    FOREIGN KEY(tecnico_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS servicios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    categoria TEXT,
    descripcion TEXT,
    tiempo_estimado TEXT,
    icono TEXT DEFAULT '🛠️',
    estado TEXT DEFAULT 'ACTIVO'
);
CREATE TABLE IF NOT EXISTS base_conocimiento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    contenido TEXT NOT NULL,
    autor_id INTEGER,
    vistas INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(autor_id) REFERENCES usuarios(id)
);
CREATE TABLE IF NOT EXISTS ans_metas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prioridad_id INTEGER UNIQUE NOT NULL,
    tiempo_respuesta_min INTEGER NOT NULL,
    tiempo_solucion_min INTEGER NOT NULL,
    FOREIGN KEY(prioridad_id) REFERENCES prioridades(id)
);
"""

def get_db():
    db_path = os.path.join(current_app.instance_path, "ecosoporte.db")
    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        db.commit()
        db.close()

def seed_db(app):
    with app.app_context():
        db = get_db()
        # Ensure all roles exist
        roles = ["ADMINISTRADOR", "SOPORTE TI", "USUARIO", "TECNICO_NIVEL_1", "TECNICO_NIVEL_2", "TECNICO_NIVEL_3", "CLIENTE"]
        for role in roles:
            db.execute("INSERT OR IGNORE INTO roles(name) VALUES (?)", (role,))

        for name, level in [("BAJA", 1), ("MEDIA", 2), ("ALTA", 3), ("CRITICA", 4)]:
            db.execute("INSERT OR IGNORE INTO prioridades(nombre,name,nivel) VALUES (?,?,?)", (name, name, level))

        for name in ["NUEVO", "ASIGNADO", "EN DIAGNÓSTICO", "EN PROCESO", "PENDIENTE", "PENDIENTE DEL USUARIO", "PENDIENTE DE TERCERO", "ESCALADO", "RESUELTO", "CERRADO", "REABIERTO"]:
            db.execute("INSERT OR IGNORE INTO estados_ticket(nombre,name) VALUES (?,?)", (name, name))

        for name in ["Hardware", "Software", "Redes", "Sistemas", "Seguridad", "Mantenimiento", "Otros"]:
            db.execute("INSERT OR IGNORE INTO categorias(nombre) VALUES (?)", (name,))

        for name in ["NIVEL 1", "NIVEL 2", "NIVEL 3"]:
            db.execute("INSERT OR IGNORE INTO niveles_soporte(nombre,name) VALUES (?,?)", (name, name))

        # Test credentials required by specification
        test_accounts = [
            ("Luis Neira", "admin@ecosoporte.com", "EcoSoporte2026!", "ADMINISTRADOR"),
            ("Soporte Técnico TI", "soporte@ecosoporte.com", "Soporte2026!", "SOPORTE TI"),
            ("Usuario Corporativo", "usuario@ecosoporte.com", "Usuario2026!", "USUARIO"),
        ]

        # Legacy admin account
        admin_email = os.getenv("ADMIN_EMAIL", "admin@ecosoportedigital.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "EcoSoporteAdmin2026!")
        test_accounts.append(("Administrador Sistema", admin_email, admin_password, "ADMINISTRADOR"))

        for name, email, pwd, role_name in test_accounts:
            role = db.execute("SELECT id FROM roles WHERE name=?", (role_name,)).fetchone()
            if role:
                exists = db.execute("SELECT id FROM usuarios WHERE lower(email)=?", (email.lower(),)).fetchone()
                if not exists:
                    db.execute("INSERT INTO usuarios(nombre,email,password_hash,role_id) VALUES (?,?,?,?)",
                               (name, email, generate_password_hash(pwd), role["id"]))
                else:
                    # Make sure password & role matches required test credentials
                    db.execute("UPDATE usuarios SET password_hash=?, role_id=? WHERE lower(email)=?",
                               (generate_password_hash(pwd), role["id"], email.lower()))

        # Seed initial servicios if empty
        if db.execute("SELECT COUNT(*) c FROM servicios").fetchone()["c"] == 0:
            sample_servicios = [
                ("Mesa de Ayuda TI", "Soporte", "Atención presencial y remota para incidentes informáticos.", "15-30 min", "🎫"),
                ("Mantenimiento Preventivo", "Infraestructura", "Limpieza, optimización y revisión diagnóstica de hardware.", "2-4 horas", "🛠️"),
                ("Administración de Redes y WiFi", "Redes", "Configuración de routers, VLANs, switches y firewalls corporativos.", "1-2 horas", "🌐"),
                ("Gestión de Usuarios y Accesos", "Seguridad", "Administración de correo, Active Directory y permisos de software.", "15 min", "🔑"),
                ("Respaldo y Seguridad de Datos", "Seguridad", "Configuración de copias de seguridad automatizadas en la nube.", "1 hora", "☁️"),
                ("Instalación de Software Corporativo", "Software", "Despliegue y licencias de suite ofimática y software especializado.", "30 min", "💻")
            ]
            for name, cat, desc, t_est, icon in sample_servicios:
                db.execute("INSERT INTO servicios(nombre,categoria,descripcion,tiempo_estimado,icono) VALUES (?,?,?,?,?)",
                           (name, cat, desc, t_est, icon))

        # Seed initial Base de Conocimiento if empty
        if db.execute("SELECT COUNT(*) c FROM base_conocimiento").fetchone()["c"] == 0:
            admin_user = db.execute("SELECT id FROM usuarios WHERE email='admin@ecosoporte.com'").fetchone()
            admin_id = admin_user["id"] if admin_user else 1
            sample_articles = [
                ("Cómo solicitar soporte técnico prioritario", "Guías", "Para crear un ticket crítico, ingresa a la sección Mis Solicitudes, selecciona la categoría correspondiente y marca la prioridad como CRÍTICA.", admin_id, 42),
                ("Solución de problemas comunes de conexión a red WiFi", "Redes", "Verifica que el adaptador esté activo, ejecuta ipconfig /renew en consola o reinicia el punto de acceso corporativo.", admin_id, 89),
                ("Configuración del correo corporativo en dispositivos móviles", "Software", "Usa los servidores IMAP/SMTP seguros indicados por el área TI. Activa la autenticación en dos pasos.", admin_id, 64),
                ("Políticas de seguridad e higienización de contraseñas", "Seguridad", "Las contraseñas deben contener al menos 8 caracteres, mayúsculas, números y símbolos. Cambiar cada 90 días.", admin_id, 110)
            ]
            for title, cat, content, aut_id, views in sample_articles:
                db.execute("INSERT INTO base_conocimiento(titulo,categoria,contenido,autor_id,vistas) VALUES (?,?,?,?,?)",
                           (title, cat, content, aut_id, views))

        # Seed initial ANS targets if empty
        if db.execute("SELECT COUNT(*) c FROM ans_metas").fetchone()["c"] == 0:
            priorities = db.execute("SELECT id, name FROM prioridades").fetchall()
            target_times = {"BAJA": (120, 1440), "MEDIA": (60, 480), "ALTA": (30, 240), "CRITICA": (15, 60)}
            for p in priorities:
                p_name = p["name"]
                if p_name in target_times:
                    resp, sol = target_times[p_name]
                    db.execute("INSERT INTO ans_metas(prioridad_id, tiempo_respuesta_min, tiempo_solucion_min) VALUES (?,?,?)",
                               (p["id"], resp, sol))

        db.commit()
        db.close()

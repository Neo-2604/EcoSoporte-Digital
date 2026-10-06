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
    nivel INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS estados_ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS niveles_soporte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT UNIQUE NOT NULL
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
    from flask import current_app
    with app.app_context():
        db = get_db()
        roles = ["ADMINISTRADOR","TECNICO_NIVEL_1","TECNICO_NIVEL_2","TECNICO_NIVEL_3","CLIENTE"]
        for role in roles:
            db.execute("INSERT OR IGNORE INTO roles(name) VALUES (?)", (role,))
        for name, level in [("BAJA",1),("MEDIA",2),("ALTA",3),("CRITICA",4)]:
            db.execute("INSERT OR IGNORE INTO prioridades(name,nivel) VALUES (?,?)",(name,level))
        for name in ["NUEVO","ASIGNADO","EN DIAGNÓSTICO","EN PROCESO","PENDIENTE","PENDIENTE DEL USUARIO","PENDIENTE DE TERCERO","ESCALADO","RESUELTO","CERRADO","REABIERTO"]:
            db.execute("INSERT OR IGNORE INTO estados_ticket(name) VALUES (?)",(name,))
        for name in ["Hardware","Software","Redes","Sistemas","Seguridad","Mantenimiento","Otros"]:
            db.execute("INSERT OR IGNORE INTO categorias(nombre) VALUES (?)",(name,))
        for name in ["NIVEL 1","NIVEL 2","NIVEL 3"]:
            db.execute("INSERT OR IGNORE INTO niveles_soporte(nombre) VALUES (?)",(name,))
        admin_email = os.getenv("ADMIN_EMAIL","admin@ecosoportedigital.com")
        admin_password = os.getenv("ADMIN_PASSWORD","EcoSoporteAdmin2026!")
        role = db.execute("SELECT id FROM roles WHERE name='ADMINISTRADOR'").fetchone()
        exists = db.execute("SELECT id FROM usuarios WHERE email=?", (admin_email,)).fetchone()
        if not exists:
            db.execute("INSERT INTO usuarios(nombre,email,password_hash,role_id) VALUES (?,?,?,?)",
                       ("Administrador",admin_email,generate_password_hash(admin_password),role["id"]))
        db.commit()
        db.close()

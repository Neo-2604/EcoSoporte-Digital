# EcoSoporte Digital

Plataforma web de soporte TI y mesa de ayuda desarrollada con Flask, SQLite, HTML, CSS y JavaScript.

## Funcionalidades

- Autenticación y cierre de sesión.
- Roles: Administrador, Técnico Nivel 1/2/3 y Cliente.
- Control de acceso por backend.
- Gestión de empresas.
- Gestión de usuarios y técnicos.
- Gestión de tickets.
- Prioridades, categorías y estados.
- Diagnósticos y soluciones.
- Escalamiento entre niveles de soporte.
- Historial de tickets.
- Equipos asociados a clientes.
- Evaluaciones de empresas por técnicos.
- Dashboard según rol.
- Modo claro/oscuro.
- Diseño responsive.
- Base SQLite inicializada automáticamente.
- Preparado para GitHub y Render mediante Gunicorn.

## Ejecutar localmente

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python run.py
```

Abrir `http://127.0.0.1:5000`.

## Administrador inicial

En desarrollo, si no existe un administrador, se crea:

- Correo: `admin@ecosoportedigital.com`
- Contraseña: `EcoSoporteAdmin2026!`

La contraseña se almacena con hash. Para producción se recomienda cambiarla mediante variables de entorno.

## Render

Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
gunicorn run:app
```

## Estructura

```text
app/
├── __init__.py
├── auth.py
├── main.py
├── admin.py
├── tickets.py
├── companies.py
├── database.py
├── decorators.py
├── templates/
└── static/
instance/
run.py
requirements.txt
.env.example
```

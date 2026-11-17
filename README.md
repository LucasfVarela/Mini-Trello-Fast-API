# Mini Trello API

API REST para organizar proyectos y tareas en un tablero estilo Trello. Cada usuario puede crear proyectos, invitar miembros, cargar tareas con prioridad y fecha de vencimiento, moverlas entre columnas y adjuntarles archivos.

## Funcionalidades

- Registro e inicio de sesión con JWT.
- Proyectos con dueño y miembros. Cada usuario ve solo los proyectos de los que forma parte.
- Tareas con estado (`todo`, `in_progress`, `done`), prioridad (`low`, `medium`, `high`), fecha de vencimiento y responsable.
- Tablero del proyecto con las tareas agrupadas por columna.
- Listado de tareas con búsqueda por título, filtros por estado, prioridad, responsable y tareas vencidas, paginación y ordenamiento.
- Vista "mis tareas" con todo lo asignado al usuario actual.
- Adjuntos por tarea con validación de tipo y tamaño.
- Permisos:
  - Solo el dueño puede editar o eliminar el proyecto y gestionar miembros.
  - Cualquier miembro puede crear y editar tareas.
  - Solo quien creó la tarea o el dueño del proyecto pueden eliminarla.
  - El responsable de una tarea tiene que ser miembro del proyecto.
- Tests automatizados con pytest.

## Tecnologías

- Python 3.10+
- FastAPI
- SQLAlchemy 2
- Pydantic v2 y pydantic-settings
- PyJWT y bcrypt
- SQLite para desarrollo local
- pytest

## Estructura

```text
app/
├── main.py
├── core/
│   ├── config.py
│   ├── db.py
│   ├── deps.py
│   └── security.py
├── models/
│   ├── attachment.py
│   ├── project.py
│   ├── task.py
│   └── user.py
├── services/
│   └── file_storage.py
└── api/
    └── v1/
        ├── access.py
        ├── auth/
        ├── projects/
        ├── tasks/
        └── attachments/
tests/
```

## Modelo de datos

```text
User ──< Project (owner)
User >──< Project (project_members)
Project ──< Task
User ──< Task (assignee, created_by)
Task ──< Attachment
```

## Instalación

### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Después de copiar el `.env`, cambiá `SECRET_KEY` por una clave larga y aleatoria. Podés generar una con:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Ejecución

```bash
uvicorn app.main:app --reload
```

La documentación interactiva queda disponible en:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Para probar los endpoints protegidos desde Swagger, registrá un usuario y usá el botón **Authorize** con tu usuario y contraseña.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/auth/register` | Registrar usuario |
| POST | `/api/v1/auth/login` | Obtener token JWT |
| GET | `/api/v1/auth/me` | Usuario actual |
| GET | `/api/v1/projects` | Listar mis proyectos |
| POST | `/api/v1/projects` | Crear proyecto |
| GET | `/api/v1/projects/{id}` | Ver proyecto |
| PATCH | `/api/v1/projects/{id}` | Editar proyecto (dueño) |
| DELETE | `/api/v1/projects/{id}` | Eliminar proyecto (dueño) |
| POST | `/api/v1/projects/{id}/members` | Agregar miembro (dueño) |
| DELETE | `/api/v1/projects/{id}/members/{user_id}` | Quitar miembro (dueño) |
| GET | `/api/v1/projects/{id}/board` | Tablero agrupado por estado |
| GET | `/api/v1/projects/{id}/tasks` | Listar tareas con filtros |
| POST | `/api/v1/projects/{id}/tasks` | Crear tarea |
| GET | `/api/v1/tasks/me` | Tareas asignadas a mí |
| GET | `/api/v1/tasks/{id}` | Ver tarea |
| PATCH | `/api/v1/tasks/{id}` | Editar tarea o moverla de columna |
| DELETE | `/api/v1/tasks/{id}` | Eliminar tarea |
| POST | `/api/v1/tasks/{id}/attachments` | Subir adjunto |
| GET | `/api/v1/tasks/{id}/attachments` | Listar adjuntos |
| GET | `/api/v1/attachments/{id}/download` | Descargar adjunto |
| DELETE | `/api/v1/attachments/{id}` | Eliminar adjunto |

### Parámetros del listado de tareas

| Parámetro | Ejemplo | Descripción |
|---|---|---|
| `status` | `in_progress` | Filtra por estado |
| `priority` | `high` | Filtra por prioridad |
| `assignee_id` | `2` | Filtra por responsable |
| `search` | `login` | Busca en el título |
| `overdue` | `true` | Solo tareas vencidas sin terminar |
| `order_by` | `due_date` | `id`, `title`, `due_date`, `priority`, `created_at` |
| `direction` | `desc` | `asc` o `desc` |
| `page` | `1` | Página |
| `size` | `10` | Resultados por página (máx. 100) |

## Ejemplo de uso con curl

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "ana", "email": "ana@example.com", "password": "password123"}'

curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -d "username=ana&password=password123"

curl -X POST http://127.0.0.1:8000/api/v1/projects \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name": "TP Final"}'

curl -X POST http://127.0.0.1:8000/api/v1/projects/1/tasks \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Diseñar la base de datos", "priority": "high", "due_date": "2026-12-01"}'

curl -X PATCH http://127.0.0.1:8000/api/v1/tasks/1 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

## Tests

```bash
pytest
```

Los tests usan una base SQLite en memoria y una carpeta temporal para los adjuntos, así que no modifican los datos locales.

## Adjuntos

Tipos permitidos: PNG, JPEG, GIF, PDF, TXT, CSV y ZIP. El tamaño máximo se configura con `MAX_UPLOAD_SIZE_MB` (5 MB por defecto). Los archivos se guardan en la carpeta `UPLOAD_DIR` con un nombre aleatorio, y se borran del disco cuando se elimina el adjunto, la tarea o el proyecto.

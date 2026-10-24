# Vehicle Parking Management System

A web-based vehicle parking management application built with **Flask** and **SQLite** as part of the **Modern Application Development I (MAD-I)** coursework.

The project organizes parking-related functionality into distinct authentication, administrator, and user modules, with server-rendered pages and database-backed persistence.

> **Project status:** Academic / development project. This repository has not been verified as production-ready.

## Contents

- [Overview](#overview)
- [Technology stack](#technology-stack)
- [Architecture](#architecture)
- [Getting started](#getting-started)
- [Database configuration](#database-configuration)
- [Project structure](#project-structure)
- [Development and security notes](#development-and-security-notes)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

Vehicle Parking Management System is a Python web application for exploring the implementation of a parking-management workflow. It separates responsibilities across three Flask blueprints:

| Module | Location | Responsibility |
| --- | --- | --- |
| Authentication | `routes/auth.py` | Authentication-related request handling |
| Administration | `routes/admin.py` | Administrator-facing request handling |
| User | `routes/user.py` | User-facing request handling |

The Flask entry point registers these blueprints and renders `templates/index.html` for the root (`/`) route.

**Scope note:** Specific workflows, such as parking reservations, billing, availability tracking, and reporting, should be confirmed against the corresponding route implementations before being represented as supported features.

## Technology stack

| Layer | Technology |
| --- | --- |
| Language | Python |
| Web framework | Flask 2.3.3 (version listed in `requirements.txt`) |
| Database | SQLite |
| ORM / database integration | Flask-SQLAlchemy, as referenced by the application code |
| Frontend | HTML templates and assets under `static/` |
| Application organization | Flask Blueprints |

## Architecture

The application follows a modular, server-rendered Flask structure:

```text
HTTP request
    |
    v
Flask application (app.py)
    |
    +-- Authentication blueprint (routes/auth.py)
    +-- Administrator blueprint (routes/admin.py)
    +-- User blueprint (routes/user.py)
    |
    v
Models / database integration (models/)
    |
    v
SQLite

HTML responses <-- templates/ + static/
```

The entry point initializes the database extension, registers the three blueprints, defines the landing-page route, and calls `db.create_all()` within an application context.

## Getting started

### Prerequisites

- Python 3 and `pip`
- Git
- A terminal (macOS, Linux, or Windows)

### 1. Clone the repository

```bash
git clone https://github.com/shobhitrajxyz/vehicle-parking.git
cd vehicle-parking
```

### 2. Create and activate a virtual environment

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

**Important:** The current `requirements.txt` declares only `Flask==2.3.3`, while `app.py` imports a database extension from `models`. If you encounter an error such as `ModuleNotFoundError: No module named 'flask_sqlalchemy'`, also install:

```bash
python -m pip install Flask-SQLAlchemy
```

The recommended repository fix is to declare the actually required database packages (and compatible versions) in `requirements.txt` so a fresh installation works using one command.

### 4. Start the application

```bash
python app.py
```

Then open:

**http://127.0.0.1:5000/**

By default, Flask's development server listens on port 5000. The current entry point enables debug mode and is intended **only for local development**.

## Database configuration

The current `app.py` sets the SQLAlchemy database URI to:

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_app.db'
```

It also initializes the database extension and invokes `db.create_all()` on application startup. With Flask-SQLAlchemy, a relative SQLite path is typically resolved against Flask's instance directory.

The repository also contains `parking.db` and a separate `setup_db.py` script referencing `sqlite:///parking.db`. These are **not the same database configuration** as the application entry point. Furthermore, `setup_db.py` imports `Base` from `models`, whereas `app.py` imports `db`.

For the normal app startup workflow, use `python app.py`. Do not assume that running `setup_db.py` initializes the same database until the two initialization paths have been reconciled.

> **Data safety:** Back up an existing SQLite database before changing the model schema or database URI. `db.create_all()` creates missing tables but does not perform schema migrations.

## Project structure

```text
vehicle-parking/
├── app.py               # Flask application entry point
├── requirements.txt     # Declared Python dependencies
├── setup_db.py          # Separate database initialization script
├── parking.db           # SQLite database file present in repository
├── models/              # Database models / integration
├── routes/              # Flask route blueprints
│   ├── auth.py          # Authentication routes
│   ├── admin.py         # Administrator routes
│   └── user.py          # User routes
├── templates/           # Server-rendered HTML templates
├── static/              # Frontend assets
├── instance/            # Flask instance-specific data
└── __pycache__/         # Generated Python bytecode cache
```

The tree above summarizes the visible repository layout and the blueprint module names imported in `app.py`; it is not a complete listing of every nested file.

## Development and security notes

Before publishing or deploying the application beyond a local learning environment:

1. **Move secrets out of source code.** The current entry point hardcodes `SECRET_KEY`. Read a securely generated value from an environment variable instead. Rotating the key will invalidate existing signed sessions.
2. **Disable debug mode in production.** Never expose the Flask development debugger publicly. Use a supported production WSGI deployment approach.
3. **Complete dependency declarations.** Pin and test the Flask-SQLAlchemy and SQLAlchemy dependencies actually used by the application.
4. **Consolidate database initialization.** Align `setup_db.py`, `app.py`, and the SQLite database path; use a migration tool for schema changes.
5. **Keep generated and sensitive files out of version control.** Add `.venv/`, `__pycache__/`, `.env`, and local runtime databases to `.gitignore` as appropriate. Review any already committed database data before publishing.
6. **Validate authentication and authorization.** Review the route implementations for password storage, access controls, CSRF protection, and input validation before real-world use.
7. **Add automated tests.** Include coverage for authentication, administrator authorization, database operations, and parking-related workflows as they are verified.

A minimal suggested `.gitignore` for future commits:

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
.env.*
!.env.example
.pytest_cache/
instance/*.db
*.sqlite3
```

This sample intentionally does **not** ignore every `*.db` file automatically; decide whether the currently committed root-level `parking.db` is sample data or a local database before changing tracking rules.

## Troubleshooting

| Problem | Suggested action |
| --- | --- |
| `ModuleNotFoundError: No module named 'flask'` | Activate your virtual environment, then install `requirements.txt`. |
| Missing `flask_sqlalchemy` module | Install `Flask-SQLAlchemy` and add the required dependency to `requirements.txt`. |
| SQLite tables missing | Verify the model imports, the configured URI, and whether `db.create_all()` completes successfully. |
| Changes appear in the wrong database | Check the difference between `parking_app.db` in `app.py` and `parking.db` in `setup_db.py`. |
| Port 5000 is already in use | Stop the process using that port, or change the development-server port in `app.py`. |
| Template not found | Confirm the expected HTML template exists under `templates/`. |

## Contributing

Issues and pull requests are welcome. For a proposed change:

1. Open an issue describing the bug or improvement, where useful.
2. Create a focused branch from `main`.
3. Implement and locally verify the change.
4. Submit a pull request explaining its purpose, validation steps, and any database or interface changes.

## License

**No license file was visible in the repository at the time this README was prepared.** Until the maintainer adds a license, do not assume the code is available under an open-source license. See [GitHub's licensing guidance](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository).

---

Developed as part of the **Modern Application Development I (MAD-I)** coursework. Source: [shobhitrajxyz/vehicle-parking](https://github.com/shobhitrajxyz/vehicle-parking).

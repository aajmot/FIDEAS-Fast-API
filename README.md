# FIDEAS Enterprise Management System API

A modern, scalable FastAPI-based enterprise management system with modular architecture.

## Project Structure

```
app/
├── __init__.py
├── main.py                 ← FastAPI application entry point
├── config/                 ← Environment, settings, constants
│   ├── settings.py
│   └── env.py
│
├── core/                   ← Global middleware, auth, common utils
│   ├── middleware/
│   │   ├── auth_middleware.py
│   │   ├── logging_middleware.py
│   │   └── cors_middleware.py
│   ├── auth/
│   │   ├── jwt_handler.py
│   │   ├── password_utils.py
│   │   └── oauth2_scheme.py
│   ├── utils/
│   │   ├── api_response.py
│   │   └── pagination.py
│   └── exceptions/
│        ├── error_handler.py
│        └── custom_exceptions.py
│
├── api/                    ← API versioning and routing
│   ├── v1/
│   │   ├── routes/
│   │   │   ├── inventory_routes.py
│   │   │   ├── accounting_routes.py
│   │   │   └── clinic_routes.py
│   │   └── schemas/
│   ├── v2/                ← Future version of APIs
│   └── public/            ← Unauthenticated endpoints
│        ├── auth_routes.py
│        └── health_routes.py
│
├── modules/                ← ERP functional modules
│   ├── inventory/
│   ├── accounting/
│   ├── clinic/
│   ├── diagnostics/
│   └── admin/
│
├── db/
│   ├── base.py
│   ├── models/
│   └── repositories/
│
└── tests/
```

## Features

- **Modular Architecture**: Clean separation of concerns with dedicated modules
- **Authentication & Authorization**: JWT-based authentication with role-based access
- **Database Integration**: SQLAlchemy ORM with PostgreSQL
- **API Versioning**: Support for multiple API versions
- **Error Handling**: Comprehensive exception handling and logging
- **Pagination**: Built-in pagination support for list endpoints
- **Health Checks**: Application and database health monitoring
- **Docker Support**: Containerized deployment ready

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Docker (optional)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd FIDEAS-Fast-API
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
python main.py
```

### Using Docker

```bash
docker build -t fideas-api .
docker run -p 8000:8000 fideas-api
```

## API Documentation

Once the application is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:password@localhost:5432/fideas_db` |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | `your-secret-key-change-in-production` |
| `API_HOST` | Server host | `0.0.0.0` |
| `API_PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `False` |

## Development

### Adding New Modules

1. Create module directory in `app/modules/`
2. Add models in `app/db/models/`
3. Create routes in `app/api/v1/routes/`
4. Register routes in `app/main.py`

### Running Tests

```bash
pytest
```

## License

This project is licensed under the MIT License.
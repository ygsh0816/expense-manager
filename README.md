# Cashcog Expense Management API

This project implements an expense management system that integrates with the Cashcog API. It consumes expense events, stores them in a database, and provides a RESTful API for clients to fetch, update, and query these expenses.

---

## Technologies Used

- **Django Ninja**: For creating the API
- **UV**: For dependency management and virtual environment
- **Pydantic**: For data validation and settings management
- **Factory Boy**: For generating test data
- **Pytest**: For running tests
- **Ruff**: For linting and formatting
- **Mypy**: For static type checking
- **Docker**: For containerization and easy deployment
- **PostgreSQL**: As the database backend

---

## Local Setup (Docker instructions provided below)

### Prerequisites

- Python 3.x
- PostgreSQL
- uv

## Setup Guide: PostgreSQL + uv on macOS

### postgreSQL

- macOS with Homebrew installed  
  If you don't have Homebrew, install it:
  ```bash
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  
- Install and start postgreSQL
   ``` 
  brew install postgresql
  brew services start postgresql
- login and create db
   ```
  psql postgres
  CREATE DATABASE expense_db;

### Install uv (Python package manager)

- Install uv via Homebrew:
  ```
  brew install astral-sh/uv/uv
  uv --version # to check if installed
  
# Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <project-directory>
   ```
2. Make virtual Env:
   ```
   make virtual_env
3. Activate the virtual_env 
   ```
   source .venv/bin/activate

4. Install dependencies using the Makefile:

   ```bash
   make install
   ```

5. Create a `.env` file by copying .env.default and set your credentials:

   ```
   cp .env.default .env
   ```
   Then open the `.env` file in a text editor and update the values, especially:
   - SECRET_KEY
   - POSTGRES_USER
   - POSTGRES_PASSWORD
   - DJANGO_SUPERUSER_USERNAME
   - DJANGO_SUPERUSER_EMAIL
   - DJANGO_SUPERUSER_PASSWORD

6. Run database migrations:

   ```bash
   python manage.py migrate
   ```

---

## Usage

1. Start the Django development server:

   ```bash
   python manage.py runserver
   ```

2. In a separate terminal, start the stream consumer:

   ```bash
   python stream_consumer/consumer.py
   ```

3. The API Docs will be available at:  
   [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

---

##  Switching Between Local and Docker Environments

> 🛑 **Important:** Be sure to configure your `.env` file correctly depending on how you're running the app.

- **For local development (without Docker):**

  ```env
  POSTGRES_HOST=localhost
  ```

- **For Docker-based development (using `docker-compose`):**

  ```env
  POSTGRES_HOST=db  # Matches the service name in docker-compose.yml
  ```

**Tip:** You can comment/uncomment these two lines in your `.env` file depending on the setup:

```env
# Local
POSTGRES_HOST=localhost
# Docker
# POSTGRES_HOST=db
```

Or vice versa:

```env
# Local
# POSTGRES_HOST=localhost
# Docker
POSTGRES_HOST=db
```


## 🐳 Docker Setup

### Prerequisites

- Docker
- Docker Compose

### Build and Run with Docker Compose

1. Ensure you have a `.env` file in your project root with required variables.

2. Build and start the services:

   ```bash
   docker-compose up -d --build
   ```

   This will:
   - Build Docker images
   - Start the PostgreSQL service
   - Start the Django web app
   - Start the stream consumer

3. Access the API Docs at:  
   [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

4. To stop the services:

   ```bash
   docker-compose down
   ```

---

##  Development Commands

The project uses a Makefile to simplify development tasks:

| Command            | Description                                                     |
|--------------------|-----------------------------------------------------------------|
| `make virtual_env` | Create a Virtual env in the current directory if does not exist |
| `make install`     | Install project dependencies                                    |
| `make test`        | Run tests using Pytest                                          |
| `make lint`        | Run lint checks with Ruff                                       |
| `make format`      | Format code using Ruff                                          |
| `make mypy`        | Run static type checks with Mypy                                |
| `make all`         | Run all checks (install + lint + format + test + typecheck)     |

Run any of these from the project root:

```bash
make <command>
```

---

## ✨ Features

- Consume and store expense events from the Cashcog API
- Validate incoming expense data
- Store expenses in PostgreSQL
- Provide RESTful endpoints to:
  - Fetch expenses
  - Update status (approve or decline)
  - Filter/query expenses

---

## 📘 API Documentation

Django Ninja automatically generates OpenAPI (Swagger) documentation for the API. You can access this interactive documentation at:

[http://localhost:8000/api/docs](http://localhost:8000/api/docs)

This documentation provides a comprehensive overview of all available endpoints, request/response formats, and allows you to test the API directly from the browser.

Key endpoints include:

- `GET /api/expenses/`: Fetch all expenses
- `GET /api/expenses/{id}/`: Fetch a specific expense
- `PUT /api/expenses/{id}/`: Update an expense (e.g., approve or decline)
- `GET /api/expenses/filter/`: Filter expenses based on various criteria

For detailed information on request parameters, response schemas, and example usage, please refer to the OpenAPI documentation.

---

## Testing

### Locally:

```bash
make test
```

### In Docker:

```bash
docker-compose run web pytest
```

---

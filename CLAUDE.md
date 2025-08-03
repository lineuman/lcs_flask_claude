# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Flask web application that provides a curl command converter with user authentication. The app features JWT-based authentication, user registration/login functionality, and a protected curl-to-Python conversion API.

## Architecture

- **Modular Flask app** (`app/`): Organized into separate modules for better maintainability
- **Service layer architecture** (`app/services/`): Business logic separated from routes and models
- **Template-based frontend** (`templates/`): Uses Jinja2 templates with Tailwind CSS styling
- **Chinese language interface**: UI is in Chinese, designed for Chinese users
- **JWT authentication**: Token-based authentication with bcrypt password hashing
- **SQLite database**: Persistent storage for users and conversion results

## Project Structure

```
app/
├── __init__.py          # Application factory
├── config/
│   ├── __init__.py
│   └── config.py        # Configuration settings
├── models/
│   ├── __init__.py
│   └── models.py        # Database models
├── services/            # Service layer - Business logic
│   ├── __init__.py
│   ├── user_service.py  # User management services
│   ├── auth_service.py  # Authentication services
│   └── converter_service.py  # Conversion services
├── auth/
│   ├── __init__.py
│   └── auth.py          # Authentication logic (legacy, migrating to services)
├── converter/
│   ├── __init__.py
│   └── converter.py     # curl to Python conversion (legacy, migrating to services)
└── routes/
    ├── __init__.py
    └── routes.py        # Route definitions (uses service layer)
templates/
├── index.html           # Main interface
├── login.html           # Login form
└── register.html        # Registration form
run.py                   # Application entry point
```

## Key Components

### Application Factory (`app/__init__.py`)
- Creates and configures Flask application
- Initializes database and JWT extensions
- Registers blueprints

### Configuration (`app/config/`)
- Environment-based configuration (development, production, testing)
- JWT and database settings
- Secret key management

### Database Models (`app/models/`)
- **User**: Stores user credentials and roles
- **ConversionResult**: Stores curl commands, converted Python code, and status
- **Relationships**: Users can have multiple conversion results

### Authentication (`app/auth/`)
- JWT token management
- User authentication and registration
- Password hashing with bcrypt
- Token blacklist for logout functionality

### Converter (`app/converter/`)
- curl command parsing logic
- Python requests code generation
- Error handling for invalid curl commands

### Service Layer (`app/services/`)
- **UserService**: User management, profile updates, password changes
- **AuthService**: Authentication, JWT token management, authorization
- **ConverterService**: curl command conversion, result storage and retrieval
- **Separation of concerns**: Business logic separated from routes and models

### Routes (`app/routes/`)
- All route definitions using blueprints
- JWT-protected endpoints
- Form and JSON request handling
- **Clean architecture**: Routes delegate to service layer for business logic

## Development Commands

```bash
# Run the application
python run.py

# Application runs on http://0.0.0.0:5000 with debug mode enabled
```

## Dependencies

The application uses a virtual environment with these key packages:
- Flask 3.1.1
- Flask-JWT-Extended (for JWT authentication)
- Flask-SQLAlchemy (for database ORM)
- bcrypt (for password hashing)
- Jinja2 3.1.6 (for templating)
- Werkzeug 3.1.3 (Flask's WSGI library)

## Default Accounts

The application automatically creates these default users on first run:
- **Admin**: username `admin`, password `admin123`, role `admin`
- **User**: username `user`, password `user123`, role `user`

## Security Considerations

- Debug mode is enabled in production configuration
- JWT secret key should be changed in production
- Default admin password should be changed in production
- No dependency management file exists - dependencies are managed in virtual environment
- Database file is stored in `instance/app.db`
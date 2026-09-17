"""
Central configuration for the Tailoring Web Application.

IMPORTANT (per BRS Section 2 / Section 31):
Nothing in the application should hard-code a Windows path or a specific
database engine. Everything goes through this file (and environment
variables), so moving from local SQLite -> MS SQL Server -> another host
later only means changing settings here / your .env file, not the code.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    # --------------------------------------------------------------
    # General
    # --------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    ENV = os.environ.get("FLASK_ENV", "development")

    # --------------------------------------------------------------
    # Database
    # --------------------------------------------------------------
    # DB_ENGINE = "sqlite" (default, works out of the box, zero setup)
    #           = "mssql"  (production target per BRS -> MS SQL Server)
    DB_ENGINE = os.environ.get("DB_ENGINE", "mssql")

    # SQLite (development / demo database - a single file, easy to inspect)
    SQLITE_PATH = os.environ.get(
        "SQLITE_PATH", str(BASE_DIR / "database" / "tailoring.db")
    )

    # MS SQL Server (production, per BRS Section 2) - used only when
    # DB_ENGINE=mssql. Requires `pip install pyodbc`.
    # Leave MSSQL_USERNAME blank to connect with Windows Authentication
    # (the default for a local SQL Server instance managed via SSMS)
    # instead of a SQL Server login.
    MSSQL_SERVER = os.environ.get("MSSQL_SERVER", "Vikas\\THEVKY")
    MSSQL_DATABASE = os.environ.get("MSSQL_DATABASE", "TailoringDB")
    MSSQL_USERNAME = os.environ.get("MSSQL_USERNAME", "")
    MSSQL_PASSWORD = os.environ.get("MSSQL_PASSWORD", "")
    MSSQL_DRIVER = os.environ.get("MSSQL_DRIVER", "ODBC Driver 17 for SQL Server")

    # --------------------------------------------------------------
    # File / Image storage (BRS Section 3)
    # --------------------------------------------------------------
    UPLOAD_ROOT = os.environ.get("UPLOAD_ROOT", str(BASE_DIR / "uploads" / "Images"))
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB max upload size
    ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

    # --------------------------------------------------------------
    # Email (BRS Section 21) - Gmail API / SMTP
    # --------------------------------------------------------------
    EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "console")  # console | smtp | gmail_api
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "techhelpvikas@gmail")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "xdhrnzbhflytpswv")
    EMAIL_FROM = os.environ.get("EMAIL_FROM", "techhelpvikas@gmail.com")

    # --------------------------------------------------------------
    # Business rules (BRS Section 24 / 41)
    # --------------------------------------------------------------
    MAX_ORDERS_PER_DAY = int(os.environ.get("MAX_ORDERS_PER_DAY", "10"))
    ADMIN_SESSION_TIMEOUT_MINUTES = int(os.environ.get("ADMIN_SESSION_TIMEOUT_MINUTES", "30"))
    MAX_LOGIN_ATTEMPTS = int(os.environ.get("MAX_LOGIN_ATTEMPTS", "5"))

    # --------------------------------------------------------------
    # Logging (BRS Section 39)
    # --------------------------------------------------------------
    LOG_DIR = os.environ.get("LOG_DIR", str(BASE_DIR / "logs"))

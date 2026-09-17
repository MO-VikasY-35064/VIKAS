"""
Thin database abstraction.

DB_ENGINE=sqlite (default) -> works instantly, no setup, great for running
this locally / demoing the full workflow end-to-end.

DB_ENGINE=mssql -> talks to MS SQL Server via pyodbc, per BRS Section 2.
Both engines are queried with the same "?" placeholder style, so the rest
of the application code (app/*.py) never needs to know which one is active.
"""

import datetime
import sqlite3
from pathlib import Path
from flask import current_app, g

# Avoid Python 3.12's sqlite3 default-adapter deprecation warning, and
# keep the stored format consistent with what SQL Server's DATETIME2
# columns accept when the same string is sent there.
sqlite3.register_adapter(datetime.datetime, lambda dt: dt.isoformat(sep=" "))
sqlite3.register_adapter(datetime.date, lambda d: d.isoformat())


def _connect_sqlite():
    path = current_app.config["SQLITE_PATH"]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _connect_mssql():
    import pyodbc  # imported lazily - only required when DB_ENGINE=mssql
    cfg = current_app.config

    # If no username is configured, use Windows Authentication (the default
    # for a local SQL Server instance managed through SSMS) instead of a
    # SQL Server login.
    if cfg.get("MSSQL_USERNAME"):
        auth_clause = f"UID={cfg['MSSQL_USERNAME']};PWD={cfg['MSSQL_PASSWORD']};"
    else:
        auth_clause = "Trusted_Connection=yes;"

    conn_str = (
        f"DRIVER={{{cfg['MSSQL_DRIVER']}}};"
        f"SERVER={cfg['MSSQL_SERVER']};"
        f"DATABASE={cfg['MSSQL_DATABASE']};"
        f"{auth_clause}"
    )
    conn = pyodbc.connect(conn_str)
    conn.timeout = 30
    return conn


def get_db():
    if "db" not in g:
        engine = current_app.config["DB_ENGINE"]
        g.db = _connect_sqlite() if engine == "sqlite" else _connect_mssql()
        g.db_engine = engine
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _rows_to_dicts(cur, rows):
    """Normalize sqlite3.Row / pyodbc.Row into plain dicts so callers can
    always use row["col"] regardless of which DB engine is active.
    sqlite3.Row already supports string-key access, but wrapping it in
    dict() here too keeps behaviour (e.g. .get(), equality, len) identical
    across both engines instead of relying on two different Row types."""
    columns = [col[0] for col in cur.description]
    return [dict(zip(columns, row)) for row in rows]


def query(sql, params=(), one=False):
    """SELECT helper. Returns a list of dicts (or a single dict if one=True)."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    raw_rows = cur.fetchall()
    rows = _rows_to_dicts(cur, raw_rows)
    cur.close()
    if one:
        return rows[0] if rows else None
    return rows


def execute(sql, params=(), commit=True):
    """
    INSERT/UPDATE/DELETE helper. For INSERTs, returns the new row's
    identity value on both engines:
      - SQLite: cursor.lastrowid
      - SQL Server: SCOPE_IDENTITY(), read back as part of the SAME batch
        as the insert (not a separate cur.execute() call afterwards).
        Without SET NOCOUNT ON, the INSERT itself emits a "rows affected"
        message alongside its actual result; firing SCOPE_IDENTITY() as a
        second, separate execute() on the same cursor can then read that
        leftover message instead and come back NULL, unpredictably,
        depending on the ODBC driver version. Batching them into one
        execute() with SET NOCOUNT ON avoids that ambiguity entirely.
    """
    conn = get_db()
    cur = conn.cursor()

    if g.get("db_engine") == "sqlite":
        cur.execute(sql, params)
        new_id = cur.lastrowid
    elif sql.lstrip().upper().startswith("INSERT"):
        batch = "SET NOCOUNT ON; " + sql + "; SELECT CAST(SCOPE_IDENTITY() AS INT) AS new_id;"
        cur.execute(batch, params)
        row = cur.fetchone()
        new_id = row[0] if row else None
    else:
        cur.execute(sql, params)
        new_id = None

    if commit:
        conn.commit()
    cur.close()
    return new_id


def upsert_setting(key, value):
    """
    Portable insert-or-update for a single website_settings row. Avoids
    SQLite-only 'ON CONFLICT ... DO UPDATE' syntax so it works unchanged
    against MS SQL Server too.
    """
    existing = query("SELECT setting_key FROM website_settings WHERE setting_key = ?", (key,), one=True)
    if existing:
        execute("UPDATE website_settings SET setting_value = ? WHERE setting_key = ?", (value, key))
    else:
        execute("INSERT INTO website_settings (setting_key, setting_value) VALUES (?, ?)", (key, value))


def init_db(app):
    """Create tables if they don't exist yet (sqlite only - for MS SQL
    Server, run database/schema_mssql.sql once against your server)."""
    app.teardown_appcontext(close_db)  # always close connections, both engines
    if app.config["DB_ENGINE"] != "sqlite":
        return
    schema_path = Path(app.root_path).parent / "database" / "schema_sqlite.sql"
    with app.app_context():
        db = get_db()
        with open(schema_path, "r") as f:
            db.executescript(f.read())
        db.commit()

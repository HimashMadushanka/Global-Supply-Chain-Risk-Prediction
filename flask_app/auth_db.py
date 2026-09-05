"""Database-backed authentication helpers for the Flask dashboard.

Set AUTH_DB_DRIVER=mysql to use MySQL. SQLite remains available as a local
fallback when the driver is not configured.
"""

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parents[1]
DB_DRIVER = os.getenv("AUTH_DB_DRIVER", "sqlite").lower()
SQLITE_PATH = Path(os.getenv("AUTH_DATABASE_PATH", BASE_DIR / "data" / "users.sqlite3"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "routexa_auth")
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": MYSQL_DATABASE,
}
SCHEMA_PATH = Path(__file__).with_name("schema.sql")
MYSQL_SCHEMA_PATH = Path(__file__).with_name("schema_mysql.sql")


def _sqlite_connect():
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(SQLITE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _mysql_connect(database=True):
    try:
        import mysql.connector
    except ImportError as exc:
        raise RuntimeError(
            "MySQL support requires mysql-connector-python. Install requirements.txt."
        ) from exc

    config = dict(MYSQL_CONFIG)
    if not database:
        config.pop("database", None)
    return mysql.connector.connect(**config)


def _mysql_cursor(connection):
    return connection.cursor(dictionary=True)


def initialize_database():
    if DB_DRIVER != "mysql":
        with _sqlite_connect() as connection:
            connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        return

    server_connection = _mysql_connect(database=False)
    try:
        cursor = server_connection.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        server_connection.commit()
        cursor.close()
    finally:
        server_connection.close()

    connection = _mysql_connect()
    try:
        cursor = connection.cursor()
        statements = MYSQL_SCHEMA_PATH.read_text(encoding="utf-8").split(";")
        for statement in statements:
            statement = statement.strip()
            if statement:
                cursor.execute(statement)
        connection.commit()
        cursor.close()
    finally:
        connection.close()


def get_user(username):
    if DB_DRIVER != "mysql":
        with _sqlite_connect() as connection:
            return connection.execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

    connection = _mysql_connect()
    try:
        cursor = _mysql_cursor(connection)
        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (username,),
        )
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def ensure_admin_user(username, password):
    initialize_database()
    if get_user(username) is not None:
        return

    password_hash = generate_password_hash(password)
    if DB_DRIVER != "mysql":
        with _sqlite_connect() as connection:
            connection.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash),
            )
        return

    connection = _mysql_connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, password_hash),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def verify_user(username, password):
    user = get_user(username)
    return user is not None and check_password_hash(user["password_hash"], password)


def update_password(username, new_password):
    password_hash = generate_password_hash(new_password)
    if DB_DRIVER != "mysql":
        with _sqlite_connect() as connection:
            connection.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE username = ?",
                (password_hash, username),
            )
        return

    connection = _mysql_connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s",
            (password_hash, username),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def create_reset_token(username, lifetime_minutes=30):
    user = get_user(username)
    if user is None:
        return None

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=lifetime_minutes)

    if DB_DRIVER != "mysql":
        with _sqlite_connect() as connection:
            connection.execute(
                "UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE user_id = ? AND used_at IS NULL",
                (user["id"],),
            )
            connection.execute(
                "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
                (user["id"], token_hash, expires_at.isoformat()),
            )
        return raw_token

    connection = _mysql_connect()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE user_id = %s AND used_at IS NULL",
            (user["id"],),
        )
        cursor.execute(
            "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (user["id"], token_hash, expires_at.replace(tzinfo=None)),
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()
    return raw_token


def consume_reset_token(raw_token, new_password):
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc)

    if DB_DRIVER != "mysql":
        with _sqlite_connect() as connection:
            token = connection.execute(
                "SELECT id, user_id, expires_at FROM password_reset_tokens WHERE token_hash = ? AND used_at IS NULL",
                (token_hash,),
            ).fetchone()
            if token is None or datetime.fromisoformat(token["expires_at"]) <= now:
                return False
            connection.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (generate_password_hash(new_password), token["user_id"]),
            )
            connection.execute(
                "UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE id = ?",
                (token["id"],),
            )
        return True

    connection = _mysql_connect()
    try:
        cursor = _mysql_cursor(connection)
        cursor.execute(
            "SELECT id, user_id, expires_at FROM password_reset_tokens WHERE token_hash = %s AND used_at IS NULL",
            (token_hash,),
        )
        token = cursor.fetchone()
        if token is None:
            return False
        expires_at = token["expires_at"].replace(tzinfo=timezone.utc)
        if expires_at <= now:
            return False
        cursor.execute(
            "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (generate_password_hash(new_password), token["user_id"]),
        )
        cursor.execute(
            "UPDATE password_reset_tokens SET used_at = CURRENT_TIMESTAMP WHERE id = %s",
            (token["id"],),
        )
        connection.commit()
        return True
    finally:
        cursor.close()
        connection.close()

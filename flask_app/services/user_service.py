from db.connection import get_connection
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
# Új felhasználó létrehozása
def create_user(username, password, is_admin=False):
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO users (username, password, is_admin)
            VALUES (%s, %s, %s)
            RETURNING username, is_admin
        """, (username, password_hash, is_admin))
        user = cur.fetchone()
        conn.commit()
        return {
            "username": user["username"],
            "is_admin": user["is_admin"]
        }

# Felhasználó lekérdezése
def get_user_by_username(username):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT username, password, is_admin, balance FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "username": row["username"],
            "password": row["password"],
            "is_admin": row["is_admin"],
            "balance": row["balance"]
        }


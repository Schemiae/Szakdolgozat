from db.connection import get_connection

# Garázsok lekérdezése az adott felhasználónak
def list_garages_for_user(username):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT g.*, 
                   (ug.garage_id IS NOT NULL) AS unlocked
            FROM garages g
            LEFT JOIN user_garages ug
              ON ug.garage_id = g.id AND ug.username = %s
            ORDER BY g.id
        """, (username,))
        return [dict(row) for row in cur.fetchall()]

# Garázs feloldása
def unlock_garage_for_user(username, garage_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM user_garages WHERE username = %s AND garage_id = %s", (username, garage_id))
        if cur.fetchone():
            return {"error": "Garage already unlocked"}, 400

        cur.execute("SELECT COUNT(*) AS cnt FROM user_garages WHERE username = %s", (username,))
        row = cur.fetchone()
        unlocked_count = (row or {}).get("cnt", 0)
        price = 0 if int(unlocked_count or 0) == 0 else 100000

        if price > 0:
            cur.execute("SELECT balance FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if not user or user["balance"] < price:
                return {"error": "Insufficient balance"}, 400
            cur.execute("UPDATE users SET balance = balance - %s WHERE username = %s", (price, username))

        cur.execute("INSERT INTO user_garages (username, garage_id) VALUES (%s, %s)", (username, garage_id))
        conn.commit()
    return {"message": "Garage unlocked"}
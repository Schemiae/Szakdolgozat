from db.connection import get_connection
from utils.validation import validate_fields

# A buszok lekérdezése az adott felhasználónak
def get_buses_for_user(username, is_admin):
    conn = get_connection()
    with conn.cursor() as cur:
        if is_admin:
            cur.execute("SELECT * FROM bus ORDER BY plate")
        else:
            cur.execute("SELECT * FROM bus WHERE owner = %s ORDER BY plate", (username,))
        rows = cur.fetchall()

    buses = []
    for row in rows:
        buses.append({
            "plate": row["plate"],
            "type": row["type"],
            "km": row["km"],
            "year": row["year"],
            "garage": row["garage"],
            "description": row["description"],
            "status": row["status"],
            "line": row["line"],
            "owner": row["owner"],
            "favourite": row["favourite"]
        })
    return buses

# Új busz létrehozása (pl.: piacon új busz vásárlásakor)
def create_bus(data):
    validate_fields(data, {
        "plate": str,
        "type": str,
        "km": int,
        "year": int,
        "garage": int,
        "description": str,
        "status": str,
        "line": str
    })
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO bus (plate, type, km, year, garage, description, status, line)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["plate"], data["type"], data["km"],
            data["year"], data["garage"], data["description"],
            data["status"], data["line"]
        ))
        conn.commit()
    return {"message": "Bus added"}

# Busz adatainak módosítása
def update_bus(plate, data):
    validate_fields(data, {
        "type": str,
        "km": int,
        "year": int,
        "garage": int,
        "description": str,
        "status": str,
        "line": str
    })

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE bus
            SET type = %s, km = %s, year = %s,
                garage = %s, description = %s, status = %s, line = %s
            WHERE plate = %s
        """, (
            data["type"],
            data["km"],
            data["year"],
            data["garage"],
            data["description"],
            data["status"],
            data["line"],
            plate
        ))
        if cur.rowcount == 0:
            return {"error": f"Bus with plate '{plate}' not found"}, 404
        
        conn.commit()

    return {"message": f"Bus with plate '{plate}' updated"}

# Kedvencek kezelése
def toggle_favourite(plate, username):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("UPDATE bus SET favourite = NOT favourite WHERE plate = %s AND owner = %s", (plate, username))
        if cur.rowcount == 0:
            return {"error": f"Bus with plate '{plate}' not found or not owned by user"}, 404
        conn.commit()
    return {"message": "Favourite toggled"}
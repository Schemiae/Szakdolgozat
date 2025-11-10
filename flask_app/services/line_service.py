from db.connection import get_connection
from utils.validation import validate_fields

def list_lines():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT name, provider_garage_id, travel_time_garage, travel_time_line
            FROM lines
            ORDER BY name
        """)
        return cur.fetchall()

def get_line(line_name):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT name, provider_garage_id, travel_time_garage, travel_time_line
            FROM lines
            WHERE name = %s
        """, (line_name,))
        return cur.fetchone()

def create_line(data):
    validate_fields(data, {
        "name": str,
        "provider_garage_id": int,
        "travel_time_garage": int,
        "travel_time_line": int
    })
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO lines (name, provider_garage_id, travel_time_garage, travel_time_line)
            VALUES (%s, %s, %s, %s)
            RETURNING name
        """, (data["name"], data["provider_garage_id"], data["travel_time_garage"], data["travel_time_line"]))
        line = cur.fetchone()
        conn.commit()
        return {"message": "Line created", "name": line["name"]}

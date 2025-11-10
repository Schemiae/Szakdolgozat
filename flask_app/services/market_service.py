from db.connection import get_connection
from utils.validation import validate_fields
import re
from datetime import datetime

# Újonnan megvásárolható modellek
NEW_BUS_MODELS = {
    "Volvo":       {"label": "Volvo 7700",        "tipus": "Volvo 7700",        "evjarat": 2004, "price": 101_000},
    "Modulo":      {"label": "Modulo M108d",      "tipus": "Modulo M108d",      "evjarat": 2008, "price": 100_000},
    "VanHool":     {"label": "VanHool AG300",     "tipus": "VanHool AG300",     "evjarat": 2002, "price": 105_000},
}

# Buszok listázása a piacon
def list_market_buses():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM bus WHERE owner IS NULL")
        return cur.fetchall()

# Új buszmodellek listázása
def list_new_bus_models():
    return [
        {"key": k, "label": v["label"], "tipus": v["tipus"], "evjarat": v["evjarat"], "price": v["price"]}
        for k, v in NEW_BUS_MODELS.items()
    ]

# Aktív hirdetések listázása
def list_active_listings():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT ml.id AS listing_id, ml.bus_plate, ml.seller_username, ml.price, ml.created_at,
                   b.type, b.km, b.year, b.garage
            FROM market_listings ml
            JOIN bus b ON b.plate = ml.bus_plate
            WHERE ml.status = 'active'
            ORDER BY ml.created_at DESC
            """
        )
        return [dict(r) for r in cur.fetchall()]

# Új hirdetés létrehozása
def create_listing(seller_username: str, bus_plate: str, price: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT owner FROM bus WHERE plate = %s", (bus_plate,))
        bus = cur.fetchone()

        if not bus or bus["owner"] != seller_username:
            return {"error": "You do not own this bus"}, 400
        
        cur.execute("SELECT 1 FROM market_listings WHERE bus_plate = %s AND status = 'active'", (bus_plate,))
        if cur.fetchone():
            return {"error": "Bus already listed"}, 400

        cur.execute(
            """
            INSERT INTO market_listings (bus_plate, seller_username, price, status)
            VALUES (%s, %s, %s, 'active')
            RETURNING id
            """,
            (bus_plate, seller_username, int(price))
        )
        row = cur.fetchone()
        conn.commit()
        return {"message": "Listing created", "listing_id": row["id"]}, 200

# Hirdetés lemondása
def cancel_listing(seller_username: str, listing_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT id, seller_username, status FROM market_listings WHERE id = %s", (listing_id,))
        row = cur.fetchone()

        if not row or row["status"] != "active":
            return {"error": "Listing not found or not active"}, 404
        
        if row["seller_username"] != seller_username:
            return {"error": "Not your listing"}, 403
        
        cur.execute("UPDATE market_listings SET status = 'canceled' WHERE id = %s", (listing_id,))
        conn.commit()
        return {"message": "Listing canceled"}, 200

# Busz megvásárlása hirdetésen keresztül
def purchase_listing(buyer_username: str, listing_id: int, garage_id=None):
    conn = get_connection()
    affected_pairs = []
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id, bus_plate, seller_username, price, status
            FROM market_listings WHERE id = %s FOR UPDATE
            """,
            (listing_id,)
        )
        listing = cur.fetchone()
        if not listing or listing["status"] != "active":
            return {"error": "Listing not available"}, 404
        
        if listing["seller_username"] == buyer_username:
            return {"error": "Cannot buy your own listing"}, 400
        

        cur.execute("SELECT owner FROM bus WHERE plate = %s", (listing["bus_plate"],))
        bus = cur.fetchone()
        if not bus or bus["owner"] != listing["seller_username"]:
            return {"error": "Seller no longer owns this bus"}, 400

        cur.execute("SELECT balance FROM users WHERE username = %s", (buyer_username,))
        buyer = cur.fetchone()
        if not buyer or buyer["balance"] < int(listing["price"]):
            return {"error": "Insufficient balance"}, 400

        target_garage = _resolve_user_garage(cur, buyer_username, garage_id)
        if target_garage is None:
            return {"error": "No unlocked garage available for storage"}, 400

        cur.execute(
            """
            SELECT DISTINCT s.line_name, s.frame
            FROM schedule_assignments sa
            JOIN schedules s ON s.id = sa.schedule_id
            WHERE sa.bus_plate = %s
            """,
            (listing["bus_plate"],)
        )
        for r in cur.fetchall() or []:
            try:
                affected_pairs.append((r["line_name"], r["frame"]))
            except Exception:
                pass
        cur.execute("DELETE FROM schedule_assignments WHERE bus_plate = %s", (listing["bus_plate"],))

        price = int(listing["price"])

        cur.execute("UPDATE users SET balance = balance - %s WHERE username = %s", (price, buyer_username))
        cur.execute("UPDATE users SET balance = balance + %s WHERE username = %s", (price, listing["seller_username"]))

        # Busz állapotának frissítése, alapjértelmezett státuszba állítása
        cur.execute(
            """
            UPDATE bus
            SET owner = %s,
                garage = %s,
                favourite = false,
                status = 'KT',
                line = '-'
            WHERE plate = %s
            """,
            (buyer_username, target_garage, listing["bus_plate"])
        )

        cur.execute("UPDATE market_listings SET status = 'sold', sold_at = %s WHERE id = %s", (datetime.utcnow(), listing_id))
        conn.commit()

    # Aktív menetrend újraszámítása az adott vonalon és idősávban
    if affected_pairs:
        try:
            from services.schedule_service import select_winner_for_line_frame
            seen = set()
            for line_name, frame in affected_pairs:
                key = (line_name, frame)
                if key in seen:
                    continue
                seen.add(key)
                select_winner_for_line_frame(line_name, frame)
        except Exception:
            pass

    return {"message": "Purchase successful"}, 200

# Busz vásárlása a régiségek listájáról
def buy_bus(bus_plate, buyer_username, price, garage_id=None):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT plate, km FROM bus WHERE plate = %s AND owner IS NULL", (bus_plate,))
        bus = cur.fetchone()
        if not bus:
            return {"error": "Bus not available"}, 400

        cur.execute("SELECT balance FROM users WHERE username = %s", (buyer_username,))
        user = cur.fetchone()
        if not user:
            return {"error": "User not found"}, 404

        if user["balance"] < price:
            return {"error": "Insufficient balance"}, 400

        target_garage = _resolve_user_garage(cur, buyer_username, garage_id)
        if target_garage is None:
            return {"error": "No unlocked garage available for storage"}, 400

        cur.execute("UPDATE users SET balance = balance - %s WHERE username = %s", (price, buyer_username))
        cur.execute(
            """
            UPDATE bus
            SET owner = %s,
                garage = %s,
                favourite = false,
                status = 'KT',
                line = '-'
            WHERE plate = %s
            """,
            (buyer_username, target_garage, bus_plate)
        )
        conn.commit()

        return {"message": f"You bought bus {bus_plate} for {price}"}, 200

# Új busz vásárlása a gyári modellek közül
def purchase_new_bus(data, buyer_username):
    validate_fields(data, {
        "model_key": str,
        "rendszam": str,
        "leiras": str,
        "garazs": int,
    })

    model = NEW_BUS_MODELS.get(data["model_key"])
    if not model:
        return {"error": "Invalid model selected"}, 400
    
    rendszam = data["rendszam"].strip().upper()
    if not re.fullmatch(r"[A-Z]{3}-\d{3}", rendszam):
        return {"error": "Invalid license plate format. Expected format: ABC-123"}, 400
    
    price = int(model["price"])
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 1 FROM user_garages WHERE username = %s AND garage_id = %s
        """, (buyer_username, data["garazs"]))
        
        if not cur.fetchone():
            return {"error": "Garage not unlocked"}, 400
        
        cur.execute("SELECT 1 FROM bus WHERE plate = %s", (rendszam,))
        if cur.fetchone():
            return {"error": "License plate already exists"}, 400
        
        cur.execute("SELECT balance FROM users WHERE username = %s", (buyer_username,))
        user = cur.fetchone()
        if not user:
            return {"error": "User not found"}, 404
        
        if user["balance"] < price:
            return {"error": "Insufficient balance"}, 400
        
        cur.execute("UPDATE users SET balance = balance - %s WHERE username = %s", (price, buyer_username))
        cur.execute(
            """
            INSERT INTO bus (plate, type, km, year, garage, description, status, line, owner, favourite)
            VALUES (%s, %s, %s, %s, %s, %s, 'KT', '-', %s, false)
            """,
            (rendszam, model["tipus"], 0, model["evjarat"], data["garazs"], data["leiras"], buyer_username)
        )
        cur.execute("SELECT balance FROM users WHERE username = %s", (buyer_username,))
        new_balance = cur.fetchone()["balance"]
        conn.commit()
    return {"message": f"You bought a new {model['label']} ({rendszam}) for {price}", "new_balance": new_balance}, 200

# Busz eladása
def sell_bus(bus_plate, seller_username, price):
    conn = get_connection()
    with conn.cursor() as cur:

        cur.execute("SELECT owner FROM bus WHERE plate = %s", (bus_plate,))
        bus = cur.fetchone()
        if not bus or bus["owner"] != seller_username:
            return {"error": "You do not own this bus"}, 400
        cur.execute("SELECT 1 FROM market_listings WHERE bus_plate = %s AND status = 'active'", (bus_plate,))
        if cur.fetchone():
            return {"error": "Bus already listed"}, 400
        cur.execute(
            """
            INSERT INTO market_listings (bus_plate, seller_username, price, status)
            VALUES (%s, %s, %s, 'active')
            """,
            (bus_plate, seller_username, int(price))
        )
        conn.commit()
        return {"message": f"Listing created for {bus_plate} at {int(price)}"}, 200

# Segédfüggvény a felhasználó garázsainak ellenőrzéséhez   
def _user_has_unlocked_garage(cur, username: str, garage_id: int) -> bool:
    cur.execute("SELECT 1 FROM user_garages WHERE username = %s AND garage_id = %s", (username, int(garage_id)))
    return cur.fetchone() is not None

# Segédfüggvény a garázs kiválasztásához
def _resolve_user_garage(cur, username: str, garage_id):
    try:
        gid = int(garage_id) if garage_id is not None and str(garage_id) != "" else None
    except Exception:
        gid = None
    if gid is not None and _user_has_unlocked_garage(cur, username, gid):
        return gid
    cur.execute("SELECT garage_id FROM user_garages WHERE username = %s ORDER BY garage_id LIMIT 1", (username,))
    row = cur.fetchone()
    return int(row["garage_id"]) if row else None
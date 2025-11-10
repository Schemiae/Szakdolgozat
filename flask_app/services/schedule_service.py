from db.connection import get_connection
from utils.validation import validate_fields
from datetime import datetime, timedelta

# Idősávok
FRAMES = {
    "morning":   ("04:00", "08:00"),
    "midday":    ("08:00", "12:00"),
    "afternoon": ("12:00", "16:00"),
    "evening":   ("16:00", "20:00"),
    "night":     ("20:00", "24:00"),
}

# Idősávokhoz tartozó szorzók
FRAME_CAP_MULTIPLIER = {
    "morning": 1.00,
    "midday": 1.15,
    "afternoon": 1.20,
    "evening": 1.20,
    "night": 1.05,
}

INTENSITY_REF = 4.0           # Gyakorisági referenciaérték
CAP_BASE = 10000              # Alapértelmezett licitkorlát
CAP_K = 10000                 # Számított licitkorlát

# Segédfüggvények a licitkorlát számításához
def _intensity_from_frequency(freq_min: int) -> float:
    f = max(1, int(freq_min))
    return 60.0 / f

def _bid_cap_for_intensity(intensity: float, frame: str | None) -> float:
    base = CAP_BASE + CAP_K * (intensity / INTENSITY_REF)
    factor = FRAME_CAP_MULTIPLIER.get(frame, 1.0) if frame else 1.0
    return base * factor

# Licitkorlát számítása adott gyakorisághoz és idősávhoz
def bid_cap_for_frequency(freq_min: int, frame: str | None = None) -> float:
    f = max(1, int(freq_min))
    intensity = 60.0 / f
    return _bid_cap_for_intensity(intensity, frame)

# Segédfüggvények az időkezeléshez
def _parse_time(s: str) -> int:
    h, m = map(int, s.split(":"))
    return (0 if h == 24 else h) * 60 + m if not (h == 24 and m == 0) else 24 * 60

def _now_minutes(now: datetime | None = None) -> int:
    dt = now or datetime.now()
    return dt.hour * 60 + dt.minute

def _frame_tick_index(now: datetime | None, start_min: int) -> int:
    now_min = _now_minutes(now)
    idx = (now_min - start_min) // 10
    return max(0, min(23, idx))

#segédfüggvény az aktuális idősáv lekéréséhez
def _current_frame(now: datetime | None = None):
    now_min = _now_minutes(now)
    for name, (start_s, end_s) in FRAMES.items():
        start_min = _parse_time(start_s)
        end_min = _parse_time(end_s)
        if start_min <= now_min < end_min:
            return name, start_min, end_min
    return None, None, None

# Kifizetés és kilóméter óra állítása az aktív menetrendekhez
def payout_for_active_schedules(now: datetime | None = None):
    frame_name, start_min, end_min = _current_frame(now)
    if not frame_name:
        return 

    tick_idx = _frame_tick_index(now, start_min)

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, username, bid_price
            FROM schedules
            WHERE status = 'active' AND frame = %s
        """, (frame_name,))
        rows = cur.fetchall()

        for row in rows:
            bid = int(row["bid_price"])
            base = bid // 24
            rem = bid % 24
            inc = base + (1 if tick_idx < rem else 0)
            if inc > 0:
                cur.execute("""
                    UPDATE users SET balance = balance + %s
                    WHERE username = %s
                """, (inc, row["username"]))
            print(f"Payout tick for frame '{frame_name}' on schedule '{row['id']}' completed, with balance: {inc}.")

            cur.execute("""
                SELECT bus_plate
                FROM schedule_assignments
                WHERE schedule_id = %s
            """, (row["id"],))
            assigned_buses = [r["bus_plate"] for r in cur.fetchall()]
            for rendszam in assigned_buses:
                cur.execute(
                    "UPDATE bus SET km = COALESCE(km, 0) + 10 WHERE plate = %s",
                    (rendszam,)
                )
            if assigned_buses:
                print(f"Updated km (+10) for {len(assigned_buses)} bus(es) on schedule {row['id']}.")

        conn.commit()

# Menetrend lekérdezése azonosító alapján
def get_schedule(schedule_id):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, username, line_name, garage_id, frame, start_time, end_time, frequency, bid_price, status
            FROM schedules
            WHERE id = %s
        """, (schedule_id,))
        return cur.fetchone()

# Menetrendek lekérdezése adott felhasználónak
def list_schedules_for_user(username):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, line_name, garage_id, start_time, end_time, frequency, bid_price, status, frame
            FROM schedules
            WHERE username = %s
            ORDER BY start_time
        """, (username,))
        rows = cur.fetchall()
        schedules = []
        for row in rows:
            schedules.append({
                "id": row["id"],
                "line_name": row["line_name"],
                "garage_id": row["garage_id"],
                "start_time": row["start_time"].strftime("%H:%M") if row["start_time"] else None,
                "end_time": row["end_time"].strftime("%H:%M") if row["end_time"] else None,
                "frequency": row["frequency"],
                "bid_price": row["bid_price"],
                "frame": row["frame"],
                "status": row["status"]
            })
        return schedules

# Új menetrend létrehozása
def create_schedule(username, data):
    validate_fields(data, {
        "line_name": str,
        "frame": str,
        "frequency": int,
        "bid_price": int
    })
    frame = data["frame"]
    if frame not in FRAMES:
        return {"error": "Invalid frame"}, 400
    start_time, end_time = FRAMES[frame]

    cap = bid_cap_for_frequency(data["frequency"], frame)
    if float(data["bid_price"]) > cap:
        return {"error": f"Bid exceeds cap ({cap:.2f}) for frequency {data['frequency']} min"}, 400

    conn = get_connection()

    with conn.cursor() as cur:
        cur.execute("SELECT provider_garage_id FROM lines WHERE name = %s", (data["line_name"],))
        line_row = cur.fetchone()
        if not line_row or line_row.get("provider_garage_id") is None:
            return {"error": f"Line '{data['line_name']}' not found or missing provider garage"}, 400
        provider_garage_id = int(line_row["provider_garage_id"])

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO schedules (username, line_name, garage_id, frame, start_time, end_time, frequency, bid_price, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
            RETURNING id, line_name, frame
        """, (
            username,
            data["line_name"],
            provider_garage_id,
            frame,
            start_time,
            end_time,
            data["frequency"],
            data["bid_price"]
        ))
        schedule = cur.fetchone()
        conn.commit()

    select_winner_for_line_frame(schedule["line_name"], schedule["frame"])
    return {"message": "Schedule created", "id": schedule["id"]}

# Menetrend módosítása
def update_schedule(schedule_id, data):
    validate_fields(data, {
        "frequency": int,
    })
    current = get_schedule(schedule_id)
    if not current:
        return {"error": "Schedule not found"}, 404
    
    cap = bid_cap_for_frequency(data["frequency"], current["frame"])
    if float(current["bid_price"]) > cap:
        return {"error": f"Current bid ({current['bid_price']}) exceeds cap ({cap:.2f}) for new frequency {data['frequency']} min"}, 400

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE schedules
            SET frequency = %s
            WHERE id = %s
            RETURNING line_name, frame
        """, (data["frequency"], schedule_id))
        updated = cur.fetchone()
        if not updated:
            return {"error": "Schedule not found"}, 404
        
        conn.commit()

    select_winner_for_line_frame(updated["line_name"], updated["frame"])
    return {"message": "Schedule updated"}

# Menetrend törlése
def delete_schedule(schedule_id):
    schedule = get_schedule(schedule_id)
    conn = get_connection()

    # Buszok visszaállítása tartalékosra
    with conn.cursor() as cur:
        cur.execute("SELECT bus_plate FROM schedule_assignments WHERE schedule_id = %s", (schedule_id,))
        for row in cur.fetchall():
            cur.execute("UPDATE bus SET status = 'KT', line = '-' WHERE plate = %s", (row["bus_plate"],))
        cur.execute("DELETE FROM schedule_assignments WHERE schedule_id = %s", (schedule_id,))
        cur.execute("DELETE FROM schedules WHERE id = %s", (schedule_id,))
        conn.commit()

    if schedule:
        select_winner_for_line_frame(schedule["line_name"], schedule["frame"])
    return {"message": "Schedule deleted"}

# A vonal futamidejének és garázsmeneti idejének lekérdezése
def get_line_times(line_name):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT travel_time_garage, travel_time_line
            FROM lines
            WHERE name = %s
        """, (line_name,))
        result = cur.fetchone()

        if result:
            return result["travel_time_garage"], result["travel_time_line"]
        return None, None

# Menetrendek lekérdezése adott vonalhoz
def list_schedules_for_line(line_name):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, username, start_time, end_time, frequency, bid_price, status, frame
            FROM schedules WHERE line_name = %s
        """, (line_name,))
        rows = cur.fetchall()
        schedules = []
        for row in rows:
            schedules.append({
                "id": row["id"],
                "username": row["username"],
                "start_time": row["start_time"].strftime("%H:%M") if row["start_time"] else None,
                "end_time": row["end_time"].strftime("%H:%M") if row["end_time"] else None,
                "frequency": row["frequency"],
                "bid_price": row["bid_price"],
                "frame": row["frame"],
                "status": row["status"]
            })
        return schedules

# Aktív menetrendek lekérdezése
def get_line_winners():
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT line_name, id, username, start_time, end_time, frequency, bid_price, frame
            FROM schedules
            WHERE status = 'active'
        """)
        rows = cur.fetchall()
        winners = []
        for row in rows:
            winners.append({
                "line_name": row["line_name"],
                "id": row["id"],
                "username": row["username"],
                "start_time": row["start_time"].strftime("%H:%M") if row["start_time"] else None,
                "end_time": row["end_time"].strftime("%H:%M") if row["end_time"] else None,
                "frequency": row["frequency"],
                "frame": row["frame"],
                "bid_price": row["bid_price"]
            })
        return winners

# Aktív menetrend kiválasztása adott vonalhoz és idősávhoz
def select_winner_for_line_frame(line_name, frame):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT id, frequency, bid_price
            FROM schedules
            WHERE line_name = %s AND frame = %s
        """, (line_name, frame))
        schedules = cur.fetchall()

        if not schedules:
            return None

        eligible = []
        for s in schedules:
            if not has_all_assignments(s["id"]):
                continue

            headway = int(s["frequency"])
            intensity = _intensity_from_frequency(headway)
            cap = _bid_cap_for_intensity(intensity, frame)
            if float(s["bid_price"]) <= cap:
                eligible.append({**s, "headway": headway, "intensity": intensity, "cap": cap})

        if not eligible:
            for s in schedules:
                cur.execute("UPDATE schedules SET status = 'pending' WHERE id = %s", (s["id"],))
            conn.commit()
            return None

        eligible.sort(key=lambda s: (-s["intensity"], float(s["bid_price"])))
        winner_id = eligible[0]["id"]
        for s in schedules:
            cur.execute(
                "UPDATE schedules SET status = %s WHERE id = %s",
                ("active" if s["id"] == winner_id else "lost", s["id"])
            )
        conn.commit()
    return winner_id

# Indulási időpontok generálása adott intervallumban és gyakorisággal
def generate_slots(start_time, end_time, frequency):
    def to_min(s: str) -> int:
        h, m = map(int, s.split(":"))
        if h == 24 and m == 0:
            return 24 * 60
        return h * 60 + m

    def to_str(mins: int) -> str:
        mins_mod = mins % (24 * 60)
        h = (mins_mod // 60) % 24
        m = mins_mod % 60
        return f"{h:02d}:{m:02d}"

    s = to_min(start_time)
    e = to_min(end_time)
    if e <= s:
        e += 24 * 60

    slots = []
    t = s
    while t <= e:
        slots.append(to_str(t))
        t += int(frequency)
    return slots

# Menetrend elosztása buszok indulásaihoz a generált indulási időpontok alapján
def plan_buses_for_schedule(schedule_id):

    schedule = get_schedule(schedule_id)
    if not schedule:
        return {"error": "Schedule not found"}, 404

    line_name = schedule["line_name"]
    travel_time_garage, travel_time_line = get_line_times(line_name)
    if travel_time_garage is None or travel_time_line is None:
        return {"error": f"Line '{line_name}' not found or missing travel times"}, 404

    travel_time_garage = int(travel_time_garage)
    travel_time_line = int(travel_time_line)

    start_time = schedule["start_time"].strftime("%H:%M") if schedule["start_time"] else None
    end_time = schedule["end_time"].strftime("%H:%M") if schedule["end_time"] else None
    frequency = int(schedule["frequency"])

    if not start_time or not end_time or frequency <= 0:
        return {"error": "Invalid schedule time window or frequency"}, 400

    slots = generate_slots(start_time, end_time, frequency)

    def to_min(tstr: str) -> int:
        h, m = map(int, tstr.split(":"))
        return h * 60 + m

    def to_str(mins: int) -> str:
        mins_mod = mins % (24 * 60) 
        h = (mins_mod // 60) % 24
        m = mins_mod % 60
        return f"{h:02d}:{m:02d}"

    slot_minutes = [to_min(s) for s in slots]

    MAX_CONTINUOUS = 240
    BREAK_MINUTES = 30

    class Bus:
        __slots__ = (
            "idx",
            "departures",
            "breaks",
            "duty_start",
            "shift_start",     
            "last_trip_end",   
            "next_available", 
        )

        def __init__(self, idx: int, first_dep: int):
            self.idx = idx
            self.departures = [first_dep]
            self.breaks = []
            self.duty_start = first_dep - travel_time_garage
            self.shift_start = self.duty_start
            self.last_trip_end = first_dep + 2 * travel_time_line
            self.next_available = self.last_trip_end

    buses = []

    for dep in slot_minutes:
        assigned = False

        buses.sort(key=lambda b: b.next_available)

        for b in buses:
            if dep < b.next_available:
                continue

            worked_since_break_at_dep = dep - b.shift_start

            if worked_since_break_at_dep >= MAX_CONTINUOUS:
                gap = dep - b.last_trip_end
                if gap >= BREAK_MINUTES:
                    break_start = b.last_trip_end
                    break_end = break_start + BREAK_MINUTES
                    b.breaks.append({"start": break_start, "end": break_end})
                    b.shift_start = break_end
                    b.next_available = max(b.next_available, break_end)

                    if dep < b.next_available:
                        continue
                    
                else:
                    continue

            b.departures.append(dep)
            b.last_trip_end = dep + 2 * travel_time_line
            b.next_available = b.last_trip_end
            assigned = True
            break

        if not assigned:
            buses.append(Bus(len(buses) + 1, dep))

    assignments = []
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT block_idx, bus_plate FROM schedule_assignments WHERE schedule_id = %s
        """, (schedule_id,))
        manual = {row["block_idx"]: row["bus_plate"] for row in cur.fetchall()}

    for idx, b in enumerate(buses):
        duty_end = b.last_trip_end + travel_time_garage 
        assignments.append({
            "bus_id": b.idx,
            "duty_start": to_str(b.duty_start),
            "duty_end": to_str(duty_end),
            "departures": [to_str(t) for t in b.departures],
            "breaks": [{"start": to_str(br["start"]), "end": to_str(br["end"])} for br in b.breaks],
            "assigned_bus": manual.get(idx) 
        })

    return {
        "schedule_id": schedule_id,
        "line_name": line_name,
        "travel_time_line": travel_time_line,
        "travel_time_garage": travel_time_garage,
        "start_time": start_time,
        "end_time": end_time,
        "frequency": frequency,
        "slots": slots,
        "buses_used": len(buses),
        "assignments": assignments,
    }

# Teljes hozzárendeltség ellenőrzése
def has_all_assignments(schedule_id):
    conn = get_connection()
    with conn.cursor() as cur:
        plan = plan_buses_for_schedule(schedule_id)
        required_blocks = len(plan["assignments"]) if plan and "assignments" in plan else 0

        cur.execute("SELECT COUNT(*) AS count FROM schedule_assignments WHERE schedule_id = %s", (schedule_id,))
        row = cur.fetchone()
        assigned_blocks = row["count"] if row and "count" in row else 0
        return assigned_blocks == required_blocks and required_blocks > 0

# Buszok menetrendi elosztásának mentése
def save_manual_assignments(schedule_id: int, assignments: dict, username: str):
    try:
        schedule = get_schedule(schedule_id)
    except Exception:
        schedule = None
    if not schedule or schedule.get("username") != username:
        return {"error": "Schedule not found or forbidden"}, 404

    # Adott busz többszöri felhasználásának ellenőrzése
    seen = set()
    for _, rendszam in (assignments or {}).items():
        if not rendszam:
            continue
        if rendszam in seen:
            return {"error": f"Bus {rendszam} is assigned to multiple blocks in this schedule."}, 400
        seen.add(rendszam)

    provider_garage = schedule.get("garage_id")

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT bus_plate FROM schedule_assignments WHERE schedule_id = %s", (schedule_id,))
        prev_assigned = {r["bus_plate"] for r in cur.fetchall()}

        for block_idx, rendszam in (assignments or {}).items():
            if not rendszam:
                continue
            cur.execute(
                """
                SELECT garage, status FROM bus
                WHERE plate = %s AND owner = %s
                """,
                (rendszam, username)
            )
            row = cur.fetchone()
            if not row:
                return {"error": f"Bus {rendszam} not found"}, 404

            if provider_garage is not None and str(row["garage"]) != str(provider_garage):
                return {"error": f"Bus {rendszam} is not in the provider garage"}, 400

            if rendszam not in prev_assigned and row["status"] != "KT":
                return {"error": f"Bus {rendszam} is not available (status {row['status']})"}, 400

        # Meglévő hozzárendelések törlése és új hozzárendelések létrehozása
        cur.execute("DELETE FROM schedule_assignments WHERE schedule_id = %s", (schedule_id,))
        new_assigned = set()
        for block_idx, rendszam in (assignments or {}).items():
            if not rendszam:
                continue
            cur.execute(
                """
                INSERT INTO schedule_assignments (schedule_id, block_idx, bus_plate)
                VALUES (%s, %s, %s)
                """,
                (schedule_id, int(block_idx), rendszam)
            )
            new_assigned.add(rendszam)

            # Kiválasztott buszok vonalra helyezése
            cur.execute(
                """
                UPDATE bus SET status = 'menetrend', line = %s
                WHERE plate = %s
                """,
                (schedule["line_name"], rendszam)
            )

        # Buszok felszabadítása
        dropped = prev_assigned - new_assigned
        for rendszam in dropped:
            cur.execute("UPDATE bus SET status = 'KT', line = '-' WHERE plate = %s", (rendszam,))

        conn.commit()

    # Aktív menetrend újraszámítása
    try:
        select_winner_for_line_frame(schedule["line_name"], schedule["frame"])
    except Exception:
        pass
    return {"message": "Assignments saved"}, 200

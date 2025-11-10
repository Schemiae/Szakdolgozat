from db.connection import get_connection
from utils.validation import validate_fields
from services.busz_service import get_buses_for_user

# Hibák listázása adott buszhoz
def list_issues_by_bus(plate: str):
    with get_connection().cursor() as cur:
        cur.execute("SELECT * FROM issues WHERE bus = %s", (plate,))
        rows = cur.fetchall()

        for row in rows:
            row["time"] = str(row["time"])
            row["repair_time"] = str(row["repair_time"])

        return rows

# Hibák listázása adott felhasználónak
def list_issues_for_user(username: str, is_admin: bool):
    buses = get_buses_for_user(username, is_admin)
    all_issues = []
    for bus in buses:
        bus_issues = list_issues_by_bus(bus["plate"])
        all_issues.extend(bus_issues)
    return all_issues

# Új hiba létrehozása
def create_issue(data):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO issues (bus, time, repair_time, repair_cost, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data["bus"], data["time"], data["repair_time"],
            int(data["repair_cost"]), data["description"]
        ))

        cur.execute("""
            SELECT DISTINCT sa.schedule_id, s.line_name, s.frame
            FROM schedule_assignments sa
            JOIN schedules s ON s.id = sa.schedule_id
            WHERE sa.bus_plate = %s
        """, (data["bus"],))
        affected = cur.fetchall() or []

        cur.execute("DELETE FROM schedule_assignments WHERE bus_plate = %s", (data["bus"],))

        cur.execute("""
            UPDATE bus SET status = 'Service', line = '-'
            WHERE plate = %s
        """, (data["bus"],))

        if affected:
            cur.executemany(
                "UPDATE schedules SET status = 'pending' WHERE id = %s AND status = 'active'",
                [(row["schedule_id"],) for row in affected]
            )

        conn.commit()
    if affected:
        try:
            from services.schedule_service import select_winner_for_line_frame
            seen = set()
            for row in affected:
                key = (row["line_name"], row["frame"])
                if key in seen:
                    continue
                seen.add(key)
                try:
                    select_winner_for_line_frame(row["line_name"], row["frame"])
                except Exception:
                    pass
        except Exception:
            pass

    return {"message": "Issue added and bus set to service"}

# Hiba törlése (pl.: javítás után)
def remove_issue(issue_id: int):
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT bus FROM issues WHERE id = %s", (issue_id,))
        row = cur.fetchone()
        if not row:
            return {"error": f"Issue with id {issue_id} not found"}
        bus_plate = row["bus"]

        cur.execute("DELETE FROM issues WHERE id = %s", (issue_id,))

        cur.execute("SELECT COUNT(*) AS issue_count FROM issues WHERE bus = %s", (bus_plate,))
        count_row = cur.fetchone()
        remaining_issues = count_row["issue_count"] if count_row else 0

        if remaining_issues == 0:
            cur.execute("""
                UPDATE bus SET status = 'KT', line = '-'
                WHERE plate = %s
            """, (bus_plate,))
            status_msg = f"and bus {bus_plate} status set to KT"
        else:
            status_msg = f"but bus {bus_plate} remains in Service due to {remaining_issues} remaining issue(s)"

        conn.commit()
    return {"message": f"Issue {issue_id} deleted, {status_msg}"}

# Minden hiba listázása
def list_all_issues():
    with get_connection().cursor() as cur:
        cur.execute("SELECT * FROM issues")
        rows = cur.fetchall() or []

        for row in rows:
            row["time"] = str(row["time"])
            row["repair_time"] = str(row["repair_time"])

        return rows
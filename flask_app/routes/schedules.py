from flask import Blueprint, jsonify, request, session
from services.schedule_service import *

schedule_bp = Blueprint("schedule", __name__)

@schedule_bp.route("/schedules", methods=["GET"])
def get_schedules():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session["username"]
    schedules = list_schedules_for_user(username)
    return jsonify(schedules)

@schedule_bp.route("/schedules/<int:schedule_id>", methods=["GET"])
def get_schedule_details(schedule_id):
    schedule = get_schedule(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404
    return jsonify(schedule)

@schedule_bp.route("/schedules", methods=["POST"])
def post_schedule():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session["username"]
    data = request.get_json()
    result = create_schedule(username, data)
    return jsonify(result)

@schedule_bp.route("/schedules/<int:schedule_id>", methods=["PUT"])
def put_schedule(schedule_id):
    data = request.get_json()
    result = update_schedule(schedule_id, data)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@schedule_bp.route("/schedules/<int:schedule_id>", methods=["DELETE"])
def delete_schedule_api(schedule_id):
    result = delete_schedule(schedule_id)
    return jsonify(result)

@schedule_bp.route("/schedules/<int:schedule_id>/assignments", methods=["GET"])
def get_schedule_assignments(schedule_id):
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session["username"]

    schedule = get_schedule(schedule_id)
    if not schedule:
        return jsonify({"error": "Schedule not found"}), 404
    if schedule.get("username") != username:
        return jsonify({"error": "Forbidden"}), 403

    try:
        result = plan_buses_for_schedule(schedule_id)
        if isinstance(result, tuple):
            return jsonify(result[0]), result[1]
        return jsonify(result)
    except Exception:
        return jsonify({"error": "Internal server error"}), 500
    
@schedule_bp.route("/schedules/<int:schedule_id>/manual_assignments", methods=["POST"])
def save_manual_assignments(schedule_id):
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session["username"]

    data = request.get_json()
    assignments = data.get("assignments", {})
    if not isinstance(assignments, dict):
        return jsonify({"error": "Invalid assignments format"}), 400

    from services.schedule_service import save_manual_assignments
    result = save_manual_assignments(schedule_id, assignments, username)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)

@schedule_bp.route("/lines/<line_name>/schedules", methods=["GET"])
def get_schedules_for_line(line_name):
    schedules = list_schedules_for_line(line_name)
    return jsonify(schedules)

@schedule_bp.route("/lines/winners", methods=["GET"])
def get_all_line_winners():
    winners = get_line_winners()
    return jsonify(winners)

@schedule_bp.route("/schedules/<int:schedule_id>", methods=["DELETE"])
def delete_schedule_route(schedule_id):
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session["username"]
    schedule = get_schedule(schedule_id)
    if not schedule or schedule["username"] != username:
        return jsonify({"error": "Schedule not found or forbidden"}), 404
    result = delete_schedule(schedule_id)
    return jsonify(result)

@schedule_bp.get("/schedules/bid-cap")
def get_bid_cap_route():
    freq = request.args.get("frequency", type=int)
    frame = request.args.get("frame", type=str)
    if not freq or freq <= 0:
        return jsonify({"error": "Invalid frequency"}), 400
    from services.schedule_service import bid_cap_for_frequency
    cap = bid_cap_for_frequency(freq, frame)
    return jsonify({"frequency": freq, "frame": frame, "cap": round(cap)})
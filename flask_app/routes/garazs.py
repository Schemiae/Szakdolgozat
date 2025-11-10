from flask import Blueprint, jsonify, request, session
from services.garage_service import list_garages_for_user, unlock_garage_for_user

garage_bp = Blueprint("garage", __name__)

@garage_bp.route("/garages", methods=["GET"])
def get_garages():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session["username"]
    garages = list_garages_for_user(username)
    return jsonify(garages)

@garage_bp.route("/garage/unlock", methods=["POST"])
def unlock_garage():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    username = session["username"]
    data = request.get_json()
    garage_id = data.get("garage_id")
    result = unlock_garage_for_user(username, garage_id)
    if "error" in result:
        return jsonify(result), result.get("status", 400)
    return jsonify(result)
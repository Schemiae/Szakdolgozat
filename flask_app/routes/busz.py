from flask import Blueprint, request, jsonify, session
from services.busz_service import *

busz_bp = Blueprint("busz", __name__)

@busz_bp.route("/buszok", methods=["GET"])
def get_buses():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    username = session["username"]
    is_admin = session.get("is_admin", False)
    buses = get_buses_for_user(username, is_admin)
    return jsonify(buses)

@busz_bp.route("/busz", methods=["POST"])
def post_bus():
    data = request.get_json()
    return jsonify(create_bus(data))

@busz_bp.route("/busz/<string:rendszam>", methods=["PUT"])
def put_bus(rendszam):
    data = request.get_json()
    return jsonify(update_bus(rendszam, data))

@busz_bp.route("/busz/<string:rendszam>/favourite", methods=["POST"])
def toggle_fav(rendszam):
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    toggle_favourite(rendszam, session["username"])
    return jsonify({"message": "Favourite toggled"})
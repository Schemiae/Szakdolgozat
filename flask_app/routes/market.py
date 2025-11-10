from flask import Blueprint, jsonify, request, session
from services.market_service import *

market_bp = Blueprint("market", __name__)

@market_bp.route("/market", methods=["GET"])
def get_market():
    return jsonify(list_market_buses())

@market_bp.route("/market/buy", methods=["POST"])
def buy_from_market():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    rendszam = data.get("rendszam")
    if not rendszam:
        return jsonify({"error": "No bus specified"}), 400

    result = buy_bus(rendszam, session["username"],data.get("price"))
    if isinstance(result, tuple):
        data, status = result
        return jsonify(data), status
    return jsonify(result)

@market_bp.route("/market/sell", methods=["POST"])
def sell_from_market():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json()
    rendszam = data.get("rendszam")
    if not rendszam:
        return jsonify({"error": "No bus specified"}), 400

    result = sell_bus(rendszam, session["username"],data.get("price"))
    if isinstance(result, tuple):
        data, status = result
        return jsonify(data), status
    return jsonify(result)

@market_bp.route("/market/models", methods=["GET"])
def get_new_bus_models():
    return jsonify(list_new_bus_models())

@market_bp.route("/market/purchase-new", methods=["POST"])
def post_purchase_new_bus():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json() or {}
    result = purchase_new_bus(data, session["username"])
    if isinstance(result, tuple):
        body, status = result
        return jsonify(body), status
    return jsonify(result)

@market_bp.route("/market/listings", methods=["GET"])
def get_market_listings():
    return jsonify(list_active_listings())

@market_bp.route("/market/list", methods=["POST"])
def post_create_listing():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json() or {}
    rendszam = data.get("rendszam")
    price = data.get("price")
    result = create_listing(session["username"], rendszam, price)
    if isinstance(result, tuple):
        body, status = result
        return jsonify(body), status
    return jsonify(result)

@market_bp.route("/market/purchase", methods=["POST"])
def post_purchase_listing():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json() or {}
    listing_id = data.get("listing_id")
    result = purchase_listing(session["username"], listing_id)
    if isinstance(result, tuple):
        body, status = result
        return jsonify(body), status
    return jsonify(result)

@market_bp.route("/market/cancel", methods=["POST"])
def post_cancel_listing():
    if "username" not in session:
        return jsonify({"error": "Not logged in"}), 401
    data = request.get_json() or {}
    listing_id = data.get("listing_id")
    result = cancel_listing(session["username"], listing_id)
    if isinstance(result, tuple):
        body, status = result
        return jsonify(body), status
    return jsonify(result)
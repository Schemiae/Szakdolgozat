from flask import Blueprint, jsonify, request, session
from services.hiba_service import *

hiba_bp = Blueprint("hiba", __name__)

@hiba_bp.route("/hiba", methods=["POST"])
def post_issue():
    data = request.get_json()
    return jsonify(create_issue(data))

@hiba_bp.route("/hiba/<int:hiba_id>", methods=["DELETE"])
def delete_issue(hiba_id):
    return jsonify(remove_issue(hiba_id))

@hiba_bp.route("/hibak/<string:plate>", methods=["GET"])
def get_issues_by_bus(plate):
    return jsonify(list_issues_by_bus(plate))

@hiba_bp.route("/hibak", methods=["GET"])
def issues():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    username = session["username"]
    is_admin = session.get("is_admin", False)
    buses = list_issues_for_user(username, is_admin)
    return jsonify(buses)

@hiba_bp.route("/hibak/all", methods=["GET"])
def get_all_issues():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(list_all_issues())
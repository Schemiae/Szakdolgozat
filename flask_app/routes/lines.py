from flask import Blueprint, jsonify, request
from services.line_service import *

lines_bp = Blueprint("lines", __name__)

@lines_bp.route("/lines", methods=["GET"])
def get_lines():
    return jsonify(list_lines())

@lines_bp.route("/lines/<string:name>", methods=["GET"])
def get_line_details(name):
    line = get_line(name)
    if not line:
        return jsonify({"error": "Line not found"}), 404
    return jsonify(line)

@lines_bp.route("/lines", methods=["POST"])
def post_line():
    data = request.get_json()
    return jsonify(create_line(data))

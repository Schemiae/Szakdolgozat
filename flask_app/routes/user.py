from flask import Blueprint, request, jsonify, session
from services.user_service import get_user_by_username, create_user
from flask_bcrypt import Bcrypt
from db.connection import get_connection

bcrypt = Bcrypt()

user_bp = Blueprint("user", __name__)

@user_bp.route("/session", methods=["GET"])
def check_session():
    if "username" in session:
        return jsonify({
            "logged_in": True,
            "username": session["username"],
            "is_admin": session.get("is_admin", False),
            "balance": session["balance"]
        })
    return jsonify({"logged_in": False})

@user_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    if get_user_by_username(username):
        return jsonify({"error": "Username already exists"}), 400

    user = create_user(username, password)
    return jsonify({"message": f"User {user['username']} registered"}), 201


@user_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = get_user_by_username(data["username"])
    if not user or not bcrypt.check_password_hash(user["password"], data["password"]):
        return jsonify({"error": "Invalid credentials"}), 401

    session["username"] = user["username"]
    session["is_admin"] = user["is_admin"]
    session["balance"] = user["balance"]
    print(session)
    return jsonify({"message": "Logged in", "balance": user["balance"]})


@user_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@user_bp.route("/user/balance", methods=["GET"])
def get_balance():
    username = session.get("username")
    if not username:
        return jsonify({"balance": None}), 401

    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT balance FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        if not user:
            return jsonify({"balance": None}), 404
        return jsonify({"balance": user["balance"]})

@user_bp.route("/user/deduct_balance", methods=["POST"])
def deduct_balance():
    if "username" not in session:
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    amount = data.get("amount")
    if not isinstance(amount, int):
        return jsonify({"error": "Invalid amount"}), 400
    conn = get_connection()
    with conn.cursor() as cur:
        cur.execute("SELECT balance FROM users WHERE username = %s", (session["username"],))
        user = cur.fetchone()
        if not user or user["balance"] < amount:
            return jsonify({"error": "Insufficient balance"}), 400
        cur.execute("UPDATE users SET balance = balance - %s WHERE username = %s", (amount, session["username"]))
        conn.commit()
    return jsonify({"message": "Balance deducted"})
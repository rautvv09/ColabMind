from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

from app.config import Config
from app.utils.db import get_collection
from app.utils.helpers import success_response, error_response

brand_bp = Blueprint("brand", __name__)

COL = "brands"


# REGISTER BRAND
@brand_bp.route("/register", methods=["POST"])
def register_brand():

    data = request.get_json() or {}

    name = data.get("brand_name")
    email = data.get("email", "").strip().lower()
    password = data.get("password")

    if not name or not email or not password:
        return error_response("Missing required fields.")

    col = get_collection(COL)

    if col.find_one({"email": email}):
        return error_response("Email already registered.")

    doc = {
        "brand_name": name,
        "email": email,
        "password": generate_password_hash(password, method="pbkdf2:sha256"),
        "created_at": datetime.utcnow()
    }

    result = col.insert_one(doc)

    return success_response(
        {"brand_id": str(result.inserted_id)},
        "Brand registered successfully.",
        201
    )


# LOGIN BRAND
@brand_bp.route("/login", methods=["POST"])
def login_brand():

    data = request.get_json() or {}

    email = data.get("email", "").strip().lower()
    password = data.get("password")

    col = get_collection(COL)

    brand = col.find_one({"email": email})

    if not brand:
        return error_response("Invalid email or password.", 401)

    if not check_password_hash(brand["password"], password):
        return error_response("Invalid email or password.", 401)

    token = jwt.encode(
        {
            "brand_id": str(brand["_id"]),
            "exp": datetime.utcnow() + timedelta(days=1)
        },
        Config.SECRET_KEY,
        algorithm="HS256"
    )

    return success_response({
        "token": token,
        "brand_id": str(brand["_id"]),
        "brand_name": brand["brand_name"]
    })
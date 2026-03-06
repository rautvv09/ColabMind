from flask import Blueprint, request, jsonify
from app.services.pricing_service import predict_price

pricing_bp = Blueprint("pricing", __name__)


@pricing_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "pricing"
    }), 200


@pricing_bp.route("/predict", methods=["POST"])
def predict():

    data = request.get_json()

    if not data or "username" not in data:
        return jsonify({
            "error": "username is required"
        }), 400

    username = data["username"].strip().lower()

    try:

        result = predict_price(username)

        return jsonify(result), 200

    except ValueError as e:

        return jsonify({
            "error": str(e)
        }), 404

    except Exception as e:

        return jsonify({
            "error": "prediction failed",
            "detail": str(e)
        }), 500
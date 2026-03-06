from flask import Blueprint, request, jsonify
from app.services.pricing_services import predict_price

pricing_bp = Blueprint("pricing", __name__, url_prefix="/api/ai/price")


@pricing_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "pricing"
    }), 200


@pricing_bp.route("/predict", methods=["POST"])
def predict():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Request body missing"
        }), 400

    username = data.get("username")

    if not username:
        return jsonify({
            "success": False,
            "message": "username is required"
        }), 400

    try:

        result = predict_price(username.strip().lower())

        return jsonify({
            "success": True,
            "data": result
        }), 200

    except ValueError as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 404

    except Exception as e:

        return jsonify({
            "success": False,
            "message": "Prediction failed",
            "detail": str(e)
        }), 500
from flask import request
import jwt

from app.config import Config
from app.utils.helpers import error_response


def get_current_brand():

    auth_header = request.headers.get("Authorization")

    if not auth_header:
        return None, error_response("Authorization header missing.", 401)

    try:

        token = auth_header.split(" ")[1]

        decoded = jwt.decode(
            token,
            Config.SECRET_KEY,
            algorithms=["HS256"]
        )

        brand_id = decoded["brand_id"]

        return brand_id, None

    except jwt.ExpiredSignatureError:
        return None, error_response("Token expired.", 401)

    except jwt.InvalidTokenError:
        return None, error_response("Invalid token.", 401)
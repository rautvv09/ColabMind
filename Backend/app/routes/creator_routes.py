from flask import Blueprint, request
from bson import ObjectId

from app.config import Config
from app.models.creator import CreatorModel
from app.utils.db import get_collection
from app.utils.helpers import serialize_doc, success_response, error_response
from app.utils.validators import is_valid_object_id, validate_required_fields

creator_bp = Blueprint("creator", __name__)

COL = Config.COLLECTION_CREATORS


# ─────────────────────────────────────────────
# POST /api/creator/register
# ─────────────────────────────────────────────
@creator_bp.route("/register", methods=["POST"])
def register_creator():

    data = request.get_json() or {}

    missing = validate_required_fields(data, ["username", "email", "niche"])
    if missing:
        return error_response(f"Missing fields: {', '.join(missing)}")

    col = get_collection(COL)

    username = data["username"].strip().lower()

    if col.find_one({"username": username}):
        return error_response("A creator with this username already exists.", 409)

    doc = CreatorModel.new(data)

    result = col.insert_one(doc)

    doc["_id"] = str(result.inserted_id)

    return success_response(doc, "Creator registered successfully.", 201)


# ─────────────────────────────────────────────
# GET /api/creator/profile/<creator_id>
# ─────────────────────────────────────────────
@creator_bp.route("/profile/<creator_id>", methods=["GET"])
def get_creator(creator_id):

    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    col = get_collection(COL)

    doc = col.find_one({"_id": ObjectId(creator_id)})

    if not doc:
        return error_response("Creator not found.", 404)

    return success_response(serialize_doc(doc))


# ─────────────────────────────────────────────
# GET /api/creator/username/<username>
# (USED BY FRONTEND SEARCH PAGE)
# ─────────────────────────────────────────────
@creator_bp.route("/username/<username>", methods=["GET"])
def get_creator_by_username(username):

    col = get_collection(COL)

    username = username.strip().lower()

    doc = col.find_one({
        "$or": [
            {"username": username},
            {"profile.username": username}
        ]
    })

    if not doc:
        return error_response("Creator not found in database.", 404)

    return success_response(serialize_doc(doc))


# ─────────────────────────────────────────────
# PUT /api/creator/profile/<creator_id>
# ─────────────────────────────────────────────
@creator_bp.route("/profile/<creator_id>", methods=["PUT"])
def update_creator(creator_id):

    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    data = request.get_json() or {}

    if not data:
        return error_response("No update data provided.")

    col = get_collection(COL)

    update = CreatorModel.update_fields(data)

    result = col.update_one(
        {"_id": ObjectId(creator_id)},
        update
    )

    if result.matched_count == 0:
        return error_response("Creator not found.", 404)

    updated = col.find_one({"_id": ObjectId(creator_id)})

    return success_response(
        serialize_doc(updated),
        "Creator updated successfully."
    )


# ─────────────────────────────────────────────
# GET /api/creator/score/<creator_id>
# ─────────────────────────────────────────────
@creator_bp.route("/score/<creator_id>", methods=["GET"])
def get_creator_score(creator_id):

    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    col = get_collection(COL)

    doc = col.find_one(
        {"_id": ObjectId(creator_id)},
        {
            "creator_score": 1,
            "engagement_rate": 1,
            "payment_reliability_index": 1
        }
    )

    if not doc:
        return error_response("Creator not found.", 404)

    return success_response({
        "creator_id": creator_id,
        "creator_score": doc.get("creator_score", 0),
        "engagement_rate": doc.get("engagement_rate", 0),
        "payment_reliability_index": doc.get("payment_reliability_index", 1)
    })


# ─────────────────────────────────────────────
# GET /api/creator/analytics/<creator_id>
# ─────────────────────────────────────────────
@creator_bp.route("/analytics/<creator_id>", methods=["GET"])
def get_creator_analytics(creator_id):

    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    col = get_collection(COL)

    doc = col.find_one({"_id": ObjectId(creator_id)})

    if not doc:
        return error_response("Creator not found.", 404)

    profile = doc.get("profile", {})

    analytics = {
        "creator_id": creator_id,
        "username": doc.get("username") or profile.get("username"),
        "followers": doc.get("follower_count") or profile.get("follower_count", 0),
        "avg_likes": doc.get("like_count_avg") or profile.get("like_count_avg", 0),
        "avg_comments": doc.get("comment_count_avg") or profile.get("comment_count_avg", 0),
        "avg_reel_views": doc.get("view_count_avg") or profile.get("view_count_avg", 0),
        "engagement_rate": doc.get("engagement_rate") or profile.get("engagement_rate", 0),
        "total_posts": doc.get("post_count") or profile.get("post_count", 0),
        "total_collaborations": doc.get("total_collaborations", 0),
        "avg_deal_value": doc.get("avg_deal_value", 0),
        "creator_score": doc.get("creator_score", 0),
        "last_synced_at": doc.get("last_synced_at")
    }

    return success_response(analytics)


# ─────────────────────────────────────────────
# GET /api/creator/all
# ─────────────────────────────────────────────
@creator_bp.route("/all", methods=["GET"])
def list_creators():

    col = get_collection(COL)

    creators = []

    for doc in col.find({}):

        profile = doc.get("profile", {})
        ml = doc.get("ml_output", {})

        followers = (
            doc.get("follower_count")
            or profile.get("follower_count")
            or doc.get("followers")
            or 0
        )

        engagement = (
            doc.get("engagement_rate")
            or profile.get("engagement_rate")
            or doc.get("engagement_%")
            or 0
        )

        score = (
            doc.get("creator_score")
            or ml.get("creator_score")
            or 0
        )

        creators.append({
            "creator_id": str(doc["_id"]),
            "username": doc.get("username") or profile.get("username"),
            "category": doc.get("category") or profile.get("category", "-"),
            "followers": followers,
            "engagement_rate": engagement,
            "creator_score": score
        })

    return success_response(creators)
   
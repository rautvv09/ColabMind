from flask import Blueprint, request
from bson import ObjectId

from app.config import Config
from app.utils.db import get_collection
from app.utils.helpers import success_response, error_response, now_iso
from app.utils.validators import is_valid_object_id

instagram_bp = Blueprint("instagram", __name__)


# ─────────────────────────────────────────────────────────────
# GET /api/instagram/fetch/<username>
# Fetch Instagram data and optionally store it for a creator
# Example:
# /api/instagram/fetch/leomessi?creator_id=<id>
# ─────────────────────────────────────────────────────────────
@instagram_bp.route("/fetch/<username>", methods=["GET"])
def fetch_instagram_profile(username):

    try:
        from app.services.instagram_service import fetch_public_profile
        metrics = fetch_public_profile(username)
    except Exception as e:
        return error_response(f"Instagram fetch failed: {str(e)}", 502)

    creator_id = request.args.get("creator_id")

    if creator_id and is_valid_object_id(creator_id):
        _sync_creator_metrics(creator_id, metrics)

    return success_response(metrics)


# ─────────────────────────────────────────────────────────────
# POST /api/instagram/sync/<creator_id>
# Re-fetch Instagram data and update MongoDB creator record
# ─────────────────────────────────────────────────────────────
@instagram_bp.route("/sync/<creator_id>", methods=["POST"])
def sync_creator(creator_id):

    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    col = get_collection(Config.COLLECTION_CREATORS)

    creator = col.find_one({"_id": ObjectId(creator_id)})

    if not creator:
        return error_response("Creator not found.", 404)

    username = creator.get("username") or creator.get("profile", {}).get("username")
    if not username:
        profile = creator.get("profile", {})
        username = profile.get("username")

    # remove spaces
    if username:
        username = username.strip()

    if not username:
        return error_response("Creator has no username set in database.")

    try:
        from app.services.instagram_service import fetch_public_profile
        metrics = fetch_public_profile(username)
    except Exception as e:
        return error_response(f"Instagram sync failed: {str(e)}", 502)

    _sync_creator_metrics(creator_id, metrics)

    return success_response(metrics, f"Synced Instagram data for @{username}.")


# ─────────────────────────────────────────────────────────────
# Internal function to update creator metrics in MongoDB
# ─────────────────────────────────────────────────────────────
def _sync_creator_metrics(creator_id: str, metrics: dict):

    col = get_collection(Config.COLLECTION_CREATORS)

    update_fields = {
        "followers": metrics.get("followers", 0),
        "following": metrics.get("following", 0),
        "total_posts": metrics.get("total_posts", 0),
        "avg_likes": metrics.get("avg_likes", 0),
        "avg_comments": metrics.get("avg_comments", 0),
        "avg_reel_views": metrics.get("avg_reel_views", 0),
        "last_synced_at": now_iso(),
    }

    col.update_one(
        {"_id": ObjectId(creator_id)},
        {"$set": update_fields}
    )
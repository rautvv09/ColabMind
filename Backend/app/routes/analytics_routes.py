from flask import Blueprint, request
from bson import ObjectId

from app.config import Config
from app.utils.db import get_collection
from app.utils.helpers import serialize_doc, success_response, error_response
from app.utils.validators import is_valid_object_id

analytics_bp = Blueprint("analytics", __name__)


# ─── GET /api/analytics/dashboard/<creator_id> ───────────────────────────────
@analytics_bp.route("/dashboard/<creator_id>", methods=["GET"])
def get_dashboard(creator_id):
    """Aggregated data bundle for the React frontend dashboard."""
    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    creator = get_collection(Config.COLLECTION_CREATORS).find_one(
        {"_id": ObjectId(creator_id)}
    )
    if not creator:
        return error_response("Creator not found.", 404)

    col_col  = get_collection(Config.COLLECTION_COLLABORATIONS)
    all_deals = list(col_col.find({"creator_id": creator_id}))

    paid_deals = [d for d in all_deals if d.get("payment_status") == "paid"]
    total_earned = sum(d.get("agreed_price", 0) for d in paid_deals)
    avg_deal     = total_earned / len(paid_deals) if paid_deals else 0

    dashboard = {
        "creator_id":       creator_id,
        "username":         creator.get("username"),
        "full_name":        creator.get("full_name"),
        "profile_pic_url":  creator.get("profile_pic_url"),
        "niche":            creator.get("niche"),

        # Metrics
        "followers":        creator.get("followers", 0),
        "engagement_rate":  creator.get("engagement_rate", 0.0),
        "creator_score":    creator.get("creator_score", 0.0),
        "posting_consistency_score": creator.get("posting_consistency_score", 0.0),

        # Deal summary
        "total_collaborations": len(all_deals),
        "completed_deals":      len(paid_deals),
        "total_earned":         round(total_earned, 2),
        "avg_deal_value":       round(avg_deal, 2),

        # Last sync
        "last_synced_at": creator.get("last_synced_at"),
    }
    return success_response(dashboard)


# ─── GET /api/analytics/engagement/<creator_id> ──────────────────────────────
@analytics_bp.route("/engagement/<creator_id>", methods=["GET"])
def get_engagement(creator_id):
    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    creator = get_collection(Config.COLLECTION_CREATORS).find_one(
        {"_id": ObjectId(creator_id)},
        {"followers": 1, "avg_likes": 1, "avg_comments": 1,
         "avg_reel_views": 1, "engagement_rate": 1, "niche": 1}
    )
    if not creator:
        return error_response("Creator not found.", 404)

    return success_response({
        "creator_id":       creator_id,
        "followers":        creator.get("followers", 0),
        "avg_likes":        creator.get("avg_likes", 0),
        "avg_comments":     creator.get("avg_comments", 0),
        "avg_reel_views":   creator.get("avg_reel_views", 0),
        "engagement_rate":  creator.get("engagement_rate", 0.0),
        "niche":            creator.get("niche"),
    })


# ─── GET /api/analytics/deals/summary/<creator_id> ───────────────────────────
@analytics_bp.route("/deals/summary/<creator_id>", methods=["GET"])
def get_deals_summary(creator_id):
    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    col_col = get_collection(Config.COLLECTION_COLLABORATIONS)
    pipeline = [
        {"$match": {"creator_id": creator_id}},
        {"$group": {
            "_id":              "$status",
            "count":            {"$sum": 1},
            "total_value":      {"$sum": "$agreed_price"},
            "avg_price":        {"$avg": "$agreed_price"},
            "avg_delay_days":   {"$avg": "$payment_delay_days"},
        }}
    ]
    results = list(col_col.aggregate(pipeline))

    # Also compute brand-wise breakdown
    brand_pipeline = [
        {"$match": {"creator_id": creator_id, "payment_status": "paid"}},
        {"$group": {
            "_id":        "$brand_id",
            "deal_count": {"$sum": 1},
            "total_paid": {"$sum": "$agreed_price"},
        }},
        {"$sort": {"total_paid": -1}},
        {"$limit": 5}
    ]
    top_brands = list(col_col.aggregate(brand_pipeline))

    return success_response({
        "creator_id":   creator_id,
        "by_status":    results,
        "top_brands":   top_brands,
    })

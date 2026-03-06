from flask import Blueprint, request
from bson import ObjectId

from app.config import Config
from app.utils.db import get_collection
from app.utils.helpers import serialize_doc, success_response, error_response
from app.utils.validators import is_valid_object_id

analytics_bp = Blueprint("analytics", __name__)

# ── Topic keyword taxonomy ─────────────────────────────────────────────────────
_TOPIC_KW = {
    "fitness":   ["fitness","gym","workout","health","yoga","training","athlete","exercise"],
    "travel":    ["travel","trip","wanderlust","explore","adventure","nature","trekking","beach"],
    "food":      ["food","foodie","recipe","cooking","restaurant","chef","eat","delicious"],
    "fashion":   ["fashion","style","ootd","outfit","clothing","wear","designer","look"],
    "tech":      ["tech","technology","coding","programming","ai","software","gadget","developer"],
    "comedy":    ["comedy","funny","meme","humor","laugh","jokes","reels","viral"],
    "sports":    ["sports","cricket","football","soccer","basketball","nba","ipl","game"],
    "lifestyle": ["lifestyle","daily","vlog","life","motivation","inspiration","mindset","wellness"],
}


def _p(doc):
    """Return (profile_dict, posts_list) from any document shape."""
    if "profile" in doc and isinstance(doc["profile"], dict):
        # Scraped shape: { profile: {...}, posts: [...] }
        return doc["profile"], doc.get("posts") or []
    # Registered shape: flat doc, no posts
    return doc, []


def _compute_topics(posts):
    """Score each topic 0-1 from post captions + hashtags."""
    n = max(len(posts), 1)
    scores = {}
    for topic, kws in _TOPIC_KW.items():
        hits = 0
        for p in posts:
            text = ((p.get("caption") or "") + " " +
                    " ".join(p.get("hashtags") or [])).lower()
            hits += sum(1 for kw in kws if kw in text)
        scores[topic] = round(min(hits / n, 1.0), 3)
    return scores


def _avg(lst):
    return round(sum(lst) / len(lst), 2) if lst else 0


# ─── GET /api/analytics/dashboard/<creator_id> ───────────────────────────────
@analytics_bp.route("/dashboard/<creator_id>", methods=["GET"])
def get_dashboard(creator_id):
    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    doc = get_collection(Config.COLLECTION_CREATORS).find_one({"_id": ObjectId(creator_id)})
    if not doc:
        return error_response("Creator not found.", 404)

    p, posts = _p(doc)

    followers = p.get("follower_count") or doc.get("follower_count") or doc.get("followers", 0)
    eng_rate  = p.get("engagement_rate") or doc.get("engagement_rate", 0.0)

    # Compute from posts when available
    if posts:
        avg_likes    = _avg([pt.get("like_count",    0) for pt in posts])
        avg_comments = _avg([pt.get("comment_count", 0) for pt in posts])
        avg_views    = _avg([pt.get("view_count",    0) for pt in posts])
        videos       = sum(1 for pt in posts if pt.get("media_type") == "video")
        images       = len(posts) - videos
        video_ratio  = round(videos / len(posts), 3)
        image_ratio  = round(images / len(posts), 3)
    else:
        avg_likes    = p.get("like_count_avg",    doc.get("avg_likes",    0))
        avg_comments = p.get("comment_count_avg", doc.get("avg_comments", 0))
        avg_views    = p.get("view_count_avg",    doc.get("avg_reel_views", 0))
        videos       = p.get("video_count", 0)
        images       = p.get("image_count", 0)
        video_ratio  = p.get("video_ratio", 0)
        image_ratio  = p.get("image_ratio", 0)

    col_col   = get_collection(Config.COLLECTION_COLLABORATIONS)
    all_deals = list(col_col.find({"creator_id": creator_id}))
    paid      = [d for d in all_deals if d.get("payment_status") == "paid"]
    earned    = sum(d.get("agreed_price", 0) for d in paid)

    return success_response({
        "creator_id":      creator_id,
        "username":        p.get("username")  or doc.get("username"),
        "full_name":       p.get("full_name") or doc.get("full_name"),
        "profile_pic_url": p.get("profile_pic_url") or doc.get("profile_pic_url"),
        "niche":           p.get("category") or doc.get("category") or doc.get("niche"),
        "followers":       followers,
        "following":       p.get("following_count") or doc.get("following_count", 0),
        "total_posts":     p.get("post_count") or doc.get("post_count", 0),
        "engagement_rate": eng_rate,
        "creator_score":   doc.get("creator_score", 0.0),
        "avg_likes":       avg_likes,
        "avg_comments":    avg_comments,
        "avg_views":       avg_views,
        "video_count":     videos,
        "image_count":     images,
        "video_ratio":     video_ratio,
        "image_ratio":     image_ratio,
        "total_collaborations": len(all_deals),
        "completed_deals":      len(paid),
        "total_earned":         round(earned, 2),
        "avg_deal_value":       round(earned / len(paid), 2) if paid else 0,
        "last_synced_at":       doc.get("last_synced_at") or doc.get("updated_at"),
    })


# ─── GET /api/analytics/engagement/<creator_id> ──────────────────────────────
@analytics_bp.route("/engagement/<creator_id>", methods=["GET"])
def get_engagement(creator_id):
    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    doc = get_collection(Config.COLLECTION_CREATORS).find_one({"_id": ObjectId(creator_id)})
    if not doc:
        return error_response("Creator not found.", 404)

    p, posts = _p(doc)

    followers = p.get("follower_count") or doc.get("follower_count") or doc.get("followers", 0)
    eng_rate  = p.get("engagement_rate") or doc.get("engagement_rate", 0.0)

    # Per-post series for area chart (P1…Pn)
    per_post = [
        {
            "label":    f"P{i + 1}",
            "likes":    int(pt.get("like_count",    0)),
            "comments": int(pt.get("comment_count", 0)),
            "views":    int(pt.get("view_count",    0)),
        }
        for i, pt in enumerate(posts)
    ]

    if posts:
        avg_likes    = _avg([pt.get("like_count",    0) for pt in posts])
        avg_comments = _avg([pt.get("comment_count", 0) for pt in posts])
        avg_views    = _avg([pt.get("view_count",    0) for pt in posts])
        videos       = sum(1 for pt in posts if pt.get("media_type") == "video")
        images       = len(posts) - videos
        video_ratio  = round(videos / len(posts), 3)
        image_ratio  = round(images / len(posts), 3)
    else:
        avg_likes    = p.get("like_count_avg",    doc.get("avg_likes",    0))
        avg_comments = p.get("comment_count_avg", doc.get("avg_comments", 0))
        avg_views    = p.get("view_count_avg",    doc.get("avg_reel_views", 0))
        videos       = p.get("video_count", 0)
        images       = p.get("image_count", 0)
        video_ratio  = p.get("video_ratio", 0)
        image_ratio  = p.get("image_ratio", 0)

    topic_scores = _compute_topics(posts)

    return success_response({
        "creator_id":    creator_id,
        "followers":     followers,
        "avg_likes":     avg_likes,
        "avg_comments":  avg_comments,
        "avg_reel_views": avg_views,
        "avg_views":     avg_views,
        "engagement_rate": eng_rate,
        "niche":         p.get("category") or doc.get("category") or doc.get("niche"),
        "per_post":      per_post,
        "posts_count":   len(posts),
        "video_count":   videos,
        "image_count":   images,
        "video_ratio":   video_ratio,
        "image_ratio":   image_ratio,
        "topic_scores":  topic_scores,
    })


# ─── GET /api/analytics/deals/summary/<creator_id> ───────────────────────────
@analytics_bp.route("/deals/summary/<creator_id>", methods=["GET"])
def get_deals_summary(creator_id):
    if not is_valid_object_id(creator_id):
        return error_response("Invalid creator ID.")

    col_col = get_collection(Config.COLLECTION_COLLABORATIONS)

    results = list(col_col.aggregate([
        {"$match": {"creator_id": creator_id}},
        {"$group": {
            "_id":            "$status",
            "count":          {"$sum": 1},
            "total_value":    {"$sum": "$agreed_price"},
            "avg_price":      {"$avg": "$agreed_price"},
            "avg_delay_days": {"$avg": "$payment_delay_days"},
        }}
    ]))

    top_brands = list(col_col.aggregate([
        {"$match": {"creator_id": creator_id, "payment_status": "paid"}},
        {"$group": {
            "_id":        "$brand_id",
            "deal_count": {"$sum": 1},
            "total_paid": {"$sum": "$agreed_price"},
        }},
        {"$sort": {"total_paid": -1}},
        {"$limit": 5},
    ]))

    return success_response({
        "creator_id": creator_id,
        "by_status":  results,
        "top_brands": top_brands,
    })
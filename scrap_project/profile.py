import requests
import math
import re
from datetime import datetime, timezone
from pymongo import MongoClient

SEARCHAPI_URL = "https://www.searchapi.io/api/v1/search"


# ══════════════════════════════════════════════════════════════
#  RAW FETCH FROM SEARCHAPI
# ══════════════════════════════════════════════════════════════

def fetch_instagram_raw(username: str, api_key: str, max_posts: int = 30) -> dict:
    """
    Hits SearchAPI instagram_profile engine and returns raw API response dict.
    Returns {"status": "not_found"} if profile missing, {"status": "error", "message": ...} on failure.
    """
    try:
        resp = requests.get(
            SEARCHAPI_URL,
            params={"engine": "instagram_profile", "username": username, "api_key": api_key},
            timeout=20,
        )
        if resp.status_code != 200:
            return {"status": "error", "message": f"API returned HTTP {resp.status_code}"}

        data    = resp.json()
        profile = data.get("profile", {})

        if not profile or not profile.get("username"):
            return {"status": "not_found"}

        posts = data.get("posts", [])[:max_posts]
        return {"status": "ok", "profile": profile, "posts": posts}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ══════════════════════════════════════════════════════════════
#  NORMALISE INTO INTERNAL DICTS
# ══════════════════════════════════════════════════════════════

def normalise_api_response(raw: dict) -> tuple[dict, list[dict]]:
    """
    Converts the flat SearchAPI profile/posts shape into the richer internal
    `user` and `posts` dicts that parse_profile() expects.
    """
    profile = raw["profile"]
    posts   = raw["posts"]

    user = {
        "username":                         profile.get("username"),
        "full_name":                        profile.get("name"),
        "id":                               profile.get("id"),
        "edge_followed_by":                 {"count": profile.get("followers", 0)},
        "edge_follow":                      {"count": profile.get("following", 0)},
        "edge_owner_to_timeline_media":     {"count": profile.get("posts", 0)},
        "is_verified":                      profile.get("verified", False),
        "is_business_account":              profile.get("is_business", False),
        "biography":                        profile.get("biography", ""),
        "external_url":                     profile.get("external_url", ""),
        "category_name":                    profile.get("category", ""),
        "profile_pic_url":                  profile.get("profile_picture", ""),
    }

    formatted_posts = []
    for post in posts:
        formatted_posts.append({
            "shortcode":              post.get("id"),
            "is_video":               post.get("type") == "reel",
            "video_view_count":       post.get("views", 0),
            "edge_liked_by":          {"count": post.get("likes", 0)},
            "edge_media_to_comment":  {"count": post.get("comments", 0)},
            "taken_at_timestamp":     int(datetime.now().timestamp()),
            "edge_media_to_caption":  {
                "edges": [{"node": {"text": post.get("caption", "")}}]
            },
        })

    return user, formatted_posts


# ══════════════════════════════════════════════════════════════
#  PARSE INTO PROFILE RECORD + POST ROWS
# ══════════════════════════════════════════════════════════════

def parse_profile(user: dict, posts: list[dict], collab_classifier=None) -> tuple[dict, list[dict]]:
    """
    Builds:
      - profile_record  : flat dict of all profile-level metrics
      - post_rows       : list of per-post dicts

    If `collab_classifier` is provided it must be a callable:
        collab_classifier(caption: str, hashtags: list[str]) -> list[str]
    and is used to enrich post rows with collab metadata.
    """
    username  = user.get("username", "")
    followers = user.get("edge_followed_by", {}).get("count", 0)
    following = user.get("edge_follow", {}).get("count", 0)
    n         = len(posts) or 1

    likes, comments, views, hashtag_counts, timestamps, media_types = [], [], [], [], [], []
    post_rows = []

    for post in posts:
        caption_edges = post.get("edge_media_to_caption", {}).get("edges", [])
        caption   = (caption_edges[0].get("node", {}).get("text", "") if caption_edges else "") or ""
        like_c    = post.get("edge_liked_by", {}).get("count", 0) or post.get("edge_media_preview_like", {}).get("count", 0)
        comment_c = post.get("edge_media_to_comment", {}).get("count", 0)
        view_c    = post.get("video_view_count", 0) or 0
        is_video  = post.get("is_video", False)
        shortcode = post.get("shortcode", "")
        timestamp = post.get("taken_at_timestamp", 0)
        ts_str    = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if timestamp else ""
        mtype     = "video" if is_video else "image"
        tags      = re.findall(r"#\w+", caption)
        eng_rate  = (like_c + comment_c) / max(followers, 1)

        likes.append(like_c); comments.append(comment_c); views.append(view_c)
        hashtag_counts.append(len(tags))
        if ts_str: timestamps.append(ts_str)
        media_types.append(mtype)

        pr = {
            "username":       username,
            "post_id":        shortcode,
            "timestamp":      ts_str,
            "media_type":     mtype,
            "like_count":     like_c,
            "comment_count":  comment_c,
            "view_count":     view_c,
            "engagement_rate": round(eng_rate, 6),
            "engagement_%":   round(eng_rate * 100, 4),
            "hashtag_count":  len(tags),
            "hashtags":       tags,
            "caption":        caption[:500],
            "post_url":       f"https://www.instagram.com/p/{shortcode}/",
        }

        # Optionally enrich with collab metadata supplied by brand.py
        if collab_classifier:
            from brand import (
                classify_collaboration, extract_brand_mentions,
                extract_promo_codes, estimate_collab_value,
                SPONSORED_HASHTAGS, SPONSORED_KEYWORDS,
            )
            mentions     = extract_brand_mentions(caption)
            codes        = extract_promo_codes(caption)
            collab_types = classify_collaboration(caption, tags)
            is_collab    = (
                any(t.lower() in SPONSORED_HASHTAGS for t in tags)
                or any(k in caption.lower() for k in SPONSORED_KEYWORDS)
            )
            est_value    = estimate_collab_value(followers, eng_rate, collab_types) if is_collab else 0
            pr.update({
                "mentions":            mentions,
                "promo_codes":         codes,
                "is_collaboration":    is_collab,
                "collab_types":        collab_types,
                "estimated_value_usd": est_value,
            })

        post_rows.append(pr)

    # ── aggregate metrics ─────────────────────────────────────
    avg_likes    = sum(likes)    / n
    avg_comments = sum(comments) / n
    avg_views    = sum(views)    / n
    eng_rate     = (avg_likes + avg_comments) / max(followers, 1)

    post_freq = 0.0
    if len(timestamps) > 1:
        first = datetime.strptime(timestamps[0],  "%Y-%m-%d %H:%M:%S")
        last  = datetime.strptime(timestamps[-1], "%Y-%m-%d %H:%M:%S")
        days  = max((last - first).days, 1)
        post_freq = round(n / days * 7, 3)

    eng_std = 0.0
    if len(likes) > 1:
        mean_l  = sum(likes) / n
        eng_std = round(math.sqrt(sum((x - mean_l) ** 2 for x in likes) / n), 2)

    video_count = media_types.count("video")

    profile_record = {
        "username":                  username,
        "full_name":                 user.get("full_name", ""),
        "user_id":                   user.get("id", ""),
        "follower_count":            followers,
        "follower_count_log":        round(math.log1p(followers), 4),
        "following_count":           following,
        "post_count":                user.get("edge_owner_to_timeline_media", {}).get("count", 0),
        "follower_following_ratio":  round(followers / max(following, 1), 3),
        "is_verified":               user.get("is_verified", False),
        "is_business":               user.get("is_business_account", False),
        "bio":                       user.get("biography", ""),
        "external_url":              user.get("external_url", ""),
        "category":                  user.get("category_name", ""),
        "profile_pic_url":           user.get("profile_pic_url", ""),
        "engagement_rate":           round(eng_rate, 6),
        "engagement_%":              round(eng_rate * 100, 4),
        "like_count_avg":            round(avg_likes, 2),
        "comment_count_avg":         round(avg_comments, 2),
        "view_count_avg":            round(avg_views, 2),
        "engagement_std":            eng_std,
        "hashtag_density_avg":       round(sum(hashtag_counts) / n, 3),
        "posting_frequency_weekly":  post_freq,
        "video_count":               video_count,
        "image_count":               n - video_count,
        "video_ratio":               round(video_count / n, 3),
        "image_ratio":               round((n - video_count) / n, 3),
        "posts_scraped":             n,
        "scraped_at":                datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }

    return profile_record, post_rows


# ══════════════════════════════════════════════════════════════
#  MONGODB — profiles collection
# ══════════════════════════════════════════════════════════════

def save_profile_to_mongodb(
    collection,
    username: str,
    profile_record: dict,
    post_rows: list[dict],
) -> str:
    """
    Upserts profile + posts into the `profiles` collection.
    Returns: "inserted" | "updated" | "no_change"
    Applies change-detection: only writes when followers or post_count changed.
    """
    now      = datetime.now(timezone.utc)
    existing = collection.find_one({"profile.username": username})

    doc = {
        "profile":    profile_record,
        "posts":      post_rows,
        "updated_at": now,
    }

    if not existing:
        collection.insert_one(doc)
        return "inserted"

    old = existing.get("profile", {})
    if (
        old.get("follower_count") != profile_record.get("follower_count")
        or old.get("post_count")  != profile_record.get("post_count")
    ):
        collection.update_one({"profile.username": username}, {"$set": doc})
        return "updated"

    return "no_change"


# ══════════════════════════════════════════════════════════════
#  HIGH-LEVEL ORCHESTRATOR
# ══════════════════════════════════════════════════════════════

def process_profile(
    username: str,
    api_key: str,
    profiles_collection=None,
    max_posts: int = 30,
    with_collab: bool = True,
) -> dict:
    """
    Full pipeline:
      1. Fetch raw data from SearchAPI
      2. Normalise & parse into profile_record + post_rows
      3. Optionally save to MongoDB profiles collection

    Returns:
      {
        "status":         "success" | "not_found" | "error",
        "action":         "inserted" | "updated" | "no_change" | None,
        "profile_record": dict,
        "post_rows":      list[dict],
        "message":        str (only on error),
      }
    """
    raw = fetch_instagram_raw(username, api_key, max_posts)

    if raw["status"] == "not_found":
        return {"status": "not_found"}
    if raw["status"] == "error":
        return {"status": "error", "message": raw["message"]}

    user, formatted_posts = normalise_api_response(raw)
    collab_fn = True if with_collab else None   # parsed inside parse_profile
    profile_record, post_rows = parse_profile(user, formatted_posts, collab_classifier=with_collab)

    action = None
    if profiles_collection is not None:
        action = save_profile_to_mongodb(profiles_collection, username, profile_record, post_rows)

    return {
        "status":         "success",
        "action":         action,
        "profile_record": profile_record,
        "post_rows":      post_rows,
    }

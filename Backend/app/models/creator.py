from app.utils.helpers import now_iso


class CreatorModel:
    """Schema factory for Creator documents."""

    COLLECTION = "creator_features"

    @staticmethod
    def new(data: dict) -> dict:
        """
        Create a new creator document.
        Supports both flattened and profile-nested Instagram data.
        """

        profile = data.get("profile", {})

        return {
            # ── Identity ─────────────────────────────────────────
            "username": (data.get("username") or profile.get("username", "")).strip().lower(),
            "full_name": data.get("full_name") or profile.get("full_name", ""),
            "email": data.get("email", ""),
            "category": data.get("category") or profile.get("category", data.get("niche", "other")),
            "bio": data.get("bio") or profile.get("bio", ""),
            "external_url": data.get("external_url") or profile.get("external_url", ""),
            "profile_pic_url": data.get("profile_pic_url") or profile.get("profile_pic_url", ""),
            "is_verified": bool(data.get("is_verified") or profile.get("is_verified", False)),
            "is_business": bool(data.get("is_business") or profile.get("is_business", False)),

            # ── Instagram Metrics ────────────────────────────────
            "follower_count": int(
                data.get("follower_count")
                or profile.get("follower_count")
                or data.get("followers", 0)
            ),

            "following_count": int(
                data.get("following_count")
                or profile.get("following_count")
                or data.get("following", 0)
            ),

            "post_count": int(
                data.get("post_count")
                or profile.get("post_count")
                or data.get("total_posts", 0)
            ),

            "like_count_avg": float(
                data.get("like_count_avg")
                or profile.get("like_count_avg")
                or data.get("avg_likes", 0)
            ),

            "comment_count_avg": float(
                data.get("comment_count_avg")
                or profile.get("comment_count_avg")
                or data.get("avg_comments", 0)
            ),

            "view_count_avg": float(
                data.get("view_count_avg")
                or profile.get("view_count_avg")
                or data.get("avg_reel_views", 0)
            ),

            "follower_following_ratio": float(
                data.get("follower_following_ratio")
                or profile.get("follower_following_ratio", 0)
            ),

            "posting_frequency_weekly": float(
                data.get("posting_frequency_weekly")
                or profile.get("posting_frequency_weekly", 0)
            ),

            "video_count": int(data.get("video_count") or profile.get("video_count", 0)),
            "image_count": int(data.get("image_count") or profile.get("image_count", 0)),
            "video_ratio": float(data.get("video_ratio") or profile.get("video_ratio", 0)),
            "hashtag_density_avg": float(
                data.get("hashtag_density_avg")
                or profile.get("hashtag_density_avg", 0)
            ),
            "engagement_std": float(
                data.get("engagement_std")
                or profile.get("engagement_std", 0)
            ),

            # ── Computed Metrics ────────────────────────────────
            "engagement_rate": float(
                data.get("engagement_rate")
                or profile.get("engagement_rate", 0.0)
            ),

            "engagement_%": float(
                data.get("engagement_%")
                or profile.get("engagement_%", 0.0)
            ),

            "follower_count_log": float(
                data.get("follower_count_log")
                or profile.get("follower_count_log", 0.0)
            ),

            "creator_score": float(data.get("creator_score", 0.0)),

            # ── Financial ───────────────────────────────────────
            "avg_deal_value": float(data.get("avg_deal_value", 0)),
            "total_collaborations": int(data.get("total_collaborations", 0)),
            "payment_reliability_index": float(data.get("payment_reliability_index", 1.0)),

            # ── Meta ───────────────────────────────────────────
            "last_synced_at": data.get("last_synced_at"),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

    @staticmethod
    def update_fields(data: dict) -> dict:
        allowed = {
            "full_name",
            "email",
            "category",
            "bio",
            "external_url",
            "profile_pic_url",
            "is_verified",
            "is_business",
            "follower_count",
            "following_count",
            "post_count",
            "like_count_avg",
            "comment_count_avg",
            "view_count_avg",
            "follower_following_ratio",
            "posting_frequency_weekly",
            "video_count",
            "image_count",
            "video_ratio",
            "hashtag_density_avg",
            "engagement_std",
            "engagement_rate",
            "engagement_%",
            "avg_deal_value",
        }

        updates = {k: v for k, v in data.items() if k in allowed}
        updates["updated_at"] = now_iso()

        return {"$set": updates}

    @staticmethod
    def normalize(doc: dict) -> dict:
        """
        Normalize old MongoDB documents
        that may contain profile.username instead of username.
        """

        profile = doc.get("profile", {})

        updates = {}

        if "username" not in doc and "username" in profile:
            updates["username"] = profile["username"]

        if "follower_count" not in doc and "follower_count" in profile:
            updates["follower_count"] = profile["follower_count"]

        if "category" not in doc and "category" in profile:
            updates["category"] = profile["category"]

        updates["updated_at"] = now_iso()

        return {"$set": updates}
from app.utils.helpers import now_iso


class BrandModel:
    """
    Schema definition and factory for Brand documents.

    Collection: brands
    """

    COLLECTION = "brands"

    @staticmethod
    def new(data: dict) -> dict:
        """Build a new brand document ready for insertion."""
        return {
            # --- Identity ---
            "name":             data.get("name", "").strip(),
            "email":            data.get("email", ""),
            "website":          data.get("website", ""),
            "industry":         data.get("industry", "other").lower(),
            "description":      data.get("description", ""),
            "logo_url":         data.get("logo_url", ""),

            # --- Payment Behavior (updated after each collaboration) ---
            "total_deals":              0,
            "completed_deals":          0,
            "avg_payment_delay_days":   0.0,   # average days late
            "late_payment_count":       0,
            "deal_completion_rate":     1.0,   # 0–1

            # --- Risk (computed by ML service) ---
            "risk_label":       "Unknown",     # Low | Medium | High | Unknown
            "risk_score":       0.0,           # raw probability from classifier

            # --- Meta ---
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

    @staticmethod
    def update_fields(data: dict) -> dict:
        """Return only the fields allowed to be updated."""
        allowed = {
            "name", "email", "website", "industry",
            "description", "logo_url"
        }
        updates = {k: v for k, v in data.items() if k in allowed}
        updates["updated_at"] = now_iso()
        return {"$set": updates}

    @staticmethod
    def update_risk(label: str, score: float) -> dict:
        """Build update dict after risk prediction."""
        return {"$set": {
            "risk_label": label,
            "risk_score": round(score, 4),
            "updated_at": now_iso()
        }}

    @staticmethod
    def record_payment(delay_days: int, was_late: bool) -> dict:
        """
        Build an $inc + $set update after a collaboration payment is recorded.
        The route handler must re-compute averages after incrementing.
        """
        inc = {
            "total_deals": 1,
            "completed_deals": 1,
            "late_payment_count": 1 if was_late else 0,
        }
        return {"$inc": inc, "$set": {"updated_at": now_iso()}}

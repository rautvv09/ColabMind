from app.utils.helpers import now_iso


class CollaborationModel:
    """
    Schema definition and factory for Collaboration documents.

    Collection: collaborations
    """

    COLLECTION = "collaborations"

    STATUSES = {"pending", "active", "completed", "cancelled"}

    @staticmethod
    def new(data: dict) -> dict:
        return {
            # --- Creator ---
            "creator_id": data.get("creator_id"),

            # --- Deal Details ---
            "deal_type": data.get("deal_type", "sponsored_post"),
            "agreed_price": float(data.get("agreed_price", 0)),
            "recommended_price": float(data.get("recommended_price", 0)),
            "currency": data.get("currency", "INR"),
            "deliverables": data.get("deliverables", []),
            "deadline": data.get("deadline"),

            # --- Status ---
            "status": "pending",

            # --- Payment ---
            "payment_status": "unpaid",
            "payment_received_on": None,
            "payment_delay_days": 0,
            "was_late": False,

            # --- Post Performance ---
            "post_likes": 0,
            "post_comments": 0,
            "post_views": 0,
            "post_url": data.get("post_url", ""),

            # --- Meta ---
            "notes": data.get("notes", ""),
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }

    @staticmethod
    def update_status(status: str):
        if status not in CollaborationModel.STATUSES:
            raise ValueError(f"Invalid status: {status}")

        return {"$set": {"status": status, "updated_at": now_iso()}}

    @staticmethod
    def record_payment(received_on: str, delay_days: int):
        return {
            "$set": {
                "payment_status": "paid",
                "payment_received_on": received_on,
                "payment_delay_days": delay_days,
                "was_late": delay_days > 0,
                "updated_at": now_iso()
            }
        }

    @staticmethod
    def update_performance(likes, comments, views, post_url=""):
        return {
            "$set": {
                "post_likes": likes,
                "post_comments": comments,
                "post_views": views,
                "post_url": post_url,
                "updated_at": now_iso()
            }
        }
from datetime import datetime


class CollaborationModel:

    @staticmethod
    def new(data):

        now = datetime.utcnow().isoformat()

        return {

            # REQUIRED FOR BRAND FILTERING
            "brand_id": data.get("brand_id"),

            "creator_id": data.get("creator_id"),

            "deal_type": data.get("deal_type", "reel"),

            "agreed_price": float(data.get("agreed_price", 0)),

            "recommended_price": float(data.get("recommended_price", 0)),

            "currency": data.get("currency", "INR"),

            "deliverables": data.get("deliverables", []),

            "deadline": data.get("deadline"),

            "status": data.get("status", "pending"),

            "payment_status": data.get("payment_status", "unpaid"),

            "payment_received_on": None,

            "payment_delay_days": 0,

            "was_late": False,

            "post_likes": 0,
            "post_comments": 0,
            "post_views": 0,
            "post_url": "",

            "notes": data.get("notes", ""),

            "created_at": now,
            "updated_at": now
        }

    # -----------------------------
    # Update collaboration status
    # -----------------------------

    @staticmethod
    def update_status(status):

        valid_status = ["pending", "active", "completed", "cancelled"]

        if status not in valid_status:
            raise ValueError("Invalid status")

        return {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
        }

    # -----------------------------
    # Record payment
    # -----------------------------

    @staticmethod
    def record_payment(received_on, delay_days):

        return {
            "$set": {
                "payment_status": "paid",
                "payment_received_on": received_on,
                "payment_delay_days": delay_days,
                "was_late": delay_days > 0,
                "updated_at": datetime.utcnow().isoformat()
            }
        }
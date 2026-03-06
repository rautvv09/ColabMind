from bson import ObjectId
from datetime import datetime


def serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-serializable dict."""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def serialize_list(docs: list) -> list:
    """Serialize a list of MongoDB documents."""
    return [serialize_doc(d) for d in docs]


def success_response(data=None, message: str = "Success", status: int = 200):
    """Standard success response format."""
    response = {"success": True, "message": message}
    if data is not None:
        response["data"] = data
    return response, status


def error_response(message: str = "An error occurred", status: int = 400):
    """Standard error response format."""
    return {"success": False, "message": message}, status


def now_iso() -> str:
    """Return current UTC timestamp as ISO string."""
    return datetime.utcnow().isoformat()


def calculate_engagement_rate(likes: float, comments: float, followers: float) -> float:
    """Calculate engagement rate as a percentage."""
    if followers == 0:
        return 0.0
    return round(((likes + comments) / followers) * 100, 4)


def calculate_posting_consistency(post_dates: list) -> float:
    """
    Score from 0–1 based on how regularly spaced posts are.
    Expects list of datetime objects sorted ascending.
    """
    if len(post_dates) < 2:
        return 0.5
    gaps = [
        (post_dates[i + 1] - post_dates[i]).days
        for i in range(len(post_dates) - 1)
    ]
    avg_gap = sum(gaps) / len(gaps)
    variance = sum((g - avg_gap) ** 2 for g in gaps) / len(gaps)
    # Lower variance = more consistent = higher score
    score = 1 / (1 + variance / 10)
    return round(score, 4)

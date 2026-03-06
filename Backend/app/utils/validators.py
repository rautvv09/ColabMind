from bson import ObjectId


def is_valid_object_id(value: str) -> bool:
    """Check if a string is a valid MongoDB ObjectId."""
    try:
        ObjectId(value)
        return True
    except Exception:
        return False


def validate_required_fields(data: dict, required: list) -> list:
    """Return list of missing fields from request data."""
    return [field for field in required if field not in data or data[field] in (None, "")]


def validate_positive_number(value, field_name: str) -> str | None:
    """Return error string if value is not a positive number, else None."""
    try:
        if float(value) < 0:
            return f"{field_name} must be a positive number."
    except (TypeError, ValueError):
        return f"{field_name} must be a valid number."
    return None


def validate_niche(niche: str) -> bool:
    """Check if niche category is one of the accepted values."""
    allowed = {
        "fashion", "beauty", "fitness", "tech", "food",
        "travel", "lifestyle", "gaming", "education", "finance", "other"
    }
    return niche.lower() in allowed


def validate_risk_label(label: str) -> bool:
    return label in {"Low", "Medium", "High"}

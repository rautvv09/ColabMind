"""
================================================================================
  Instagram Influencer Feature Engineering Pipeline
  End-to-End Implementation
================================================================================
  Stages:
    0.  Eligibility Filter
    1.  Data Cleaning
    2.  Post-Level Feature Extraction
    3.  Profile-Level Aggregation
    4.  Temporal Activity Features
    5.  Audience & Growth Features
    6.  Content Topic Features
    7.  Collaboration Features
    8.  Creator Authority Features
    9.  Brand Risk Features
    10. Final ML Feature Vector Assembly
    11. ML Model Stubs (XGBoost, RF, Scorer)
    12. MongoDB Storage Helper
================================================================================
"""

import re
import math
import statistics
from datetime import datetime, timedelta
from typing import Optional
import unicodedata

# ---------------------------------------------------------------------------
# Optional heavy dependencies — gracefully degraded if not installed
# ---------------------------------------------------------------------------
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from pymongo import MongoClient
    HAS_MONGO = True
except ImportError:
    HAS_MONGO = False

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ============================================================================
#  CONSTANTS
# ============================================================================

INFLUENCER_TIERS = [
    ("mega",   10_000_000, float("inf")),
    ("macro",   1_000_000, 10_000_000),
    ("mid",       100_000,  1_000_000),
    ("micro",      10_000,    100_000),
    ("nano",        1_000,     10_000),
]

TOPIC_TAXONOMY = {
    "fitness":   ["fitness", "gym", "workout", "health", "yoga", "training", "athlete"],
    "travel":    ["travel", "trip", "wanderlust", "explore", "trekking", "adventure", "nature"],
    "food":      ["food", "foodie", "recipe", "cooking", "restaurant", "chef", "eat"],
    "fashion":   ["fashion", "style", "ootd", "outfit", "clothing", "wear", "designer"],
    "tech":      ["tech", "technology", "coding", "programming", "ai", "software", "gadget"],
    "comedy":    ["comedy", "funny", "meme", "humor", "laugh", "jokes", "reels"],
    "sports":    ["sports", "cricket", "football", "soccer", "basketball", "nba", "ipl"],
    "lifestyle": ["lifestyle", "daily", "vlog", "life", "motivation", "inspiration", "mindset"],
}

BRAND_RISK_KEYWORDS = {
    "controversial": ["controversy", "scandal", "banned", "illegal", "drugs", "violence"],
    "political":     ["politics", "government", "election", "vote", "minister", "bjp", "congress"],
    "sensitive":     ["religion", "caste", "communal", "offensive", "nsfw", "adult"],
    "toxic":         ["hate", "abuse", "slur", "harassment", "threat", "racist"],
}

SPONSORED_PATTERNS = [
    r"#ad\b", r"#sponsored", r"#paidpartnership", r"#gifted",
    r"\[ad\]", r"\[sponsored\]", r"paid promotion", r"in partnership with",
    r"collab with", r"collaboration with", r"partnered with",
]

PROMO_CODE_PATTERN = re.compile(
    r"\b(use|code|promo|discount|coupon|offer)[:\s]+([A-Z0-9]{4,15})\b", re.IGNORECASE
)

AFFILIATE_LINK_PATTERN = re.compile(
    r"(amzn\.to|bit\.ly|goo\.gl|shorturl|linktr\.ee|linkinbio|shop\.ly)", re.IGNORECASE
)

MEDIA_TYPE_MAP = {"IMAGE": 0, "VIDEO": 1, "CAROUSEL": 2}

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F9FF"
    "\U00002700-\U000027BF"
    "\U0001FA00-\U0001FA6F"
    "]+",
    flags=re.UNICODE,
)


# ============================================================================
#  STAGE 0 — ELIGIBILITY FILTER
# ============================================================================

def classify_influencer_tier(follower_count: int) -> str:
    """Return the influencer tier label based on follower count."""
    for tier_name, low, high in INFLUENCER_TIERS:
        if low <= follower_count < high:
            return tier_name
    return "none"


def _min_engagement_threshold(follower_count: int) -> float:
    """
    Tiered minimum engagement rate.
    Mega/macro influencers naturally have lower engagement — industry standard:
        nano/micro  (< 100K)   : >= 1.0%
        mid         (100K–1M)  : >= 0.5%
        macro/mega  (1M+)      : >= 0.1%
    """
    if follower_count >= 1_000_000:
        return 0.001   # 0.1%
    if follower_count >= 100_000:
        return 0.005   # 0.5%
    return 0.01        # 1.0%


def is_valid_influencer(profile: dict, strict: bool = False) -> bool:
    """
    Deterministic pre-filter applied BEFORE any ML processing.

    Baseline rules:
        follower_count           >= 1,000
        follower_following_ratio >= 2
        engagement_rate          >= tiered threshold (see _min_engagement_threshold)

    Strict (production) rules additionally require:
        follower_count           >= 5,000
        posts_scraped            >= 8
    """
    followers = profile.get("follower_count", 0)
    ratio     = profile.get("follower_following_ratio", 0)
    eng_rate  = profile.get("engagement_rate", 0)
    scraped   = profile.get("posts_scraped", 0)

    if followers < 1_000:
        return False
    if ratio < 2:
        return False

    min_eng = _min_engagement_threshold(followers)
    if eng_rate < min_eng:
        return False

    if strict:
        if followers < 5_000:
            return False
        if scraped < 8:
            return False

    return True


def apply_eligibility_filter(raw_document: dict, strict: bool = False) -> dict:
    """
    Attach eligibility metadata to the top-level document and return it.
    Downstream stages should respect `influencer_valid = False`.
    """
    profile   = raw_document.get("profile", {})
    followers = profile.get("follower_count", 0)
    valid     = is_valid_influencer(profile, strict=strict)
    tier      = classify_influencer_tier(followers) if valid else "none"

    raw_document["influencer_valid"] = valid
    raw_document["influencer_tier"]  = tier
    raw_document["creator_type"]     = (
        f"{tier.upper()}_INFLUENCER" if valid else "NON_INFLUENCER"
    )
    raw_document["paid_collab_eligible"] = valid
    return raw_document


# ============================================================================
#  STAGE 1 — DATA CLEANING
# ============================================================================

def _safe_int(val, default: int = 0) -> int:
    try:
        return int(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _safe_float(val, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def _normalize_timestamp(ts) -> Optional[datetime]:
    """Convert string / epoch timestamps to datetime objects."""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%fZ"):
        try:
            return datetime.strptime(str(ts), fmt)
        except ValueError:
            continue
    try:
        return datetime.utcfromtimestamp(float(ts))
    except (ValueError, OSError):
        return None


def _strip_emoji(text: str) -> str:
    return EMOJI_PATTERN.sub("", text).strip()


def _deduplicate_hashtags(hashtags: list) -> list:
    seen, result = set(), []
    for tag in hashtags:
        normalized = tag.lower().strip()
        if normalized not in seen:
            seen.add(normalized)
            result.append(tag)
    return result


def clean_post(post: dict) -> dict:
    """Stage 1: Normalize a single raw post record."""
    cleaned = dict(post)

    # Null-safe metrics
    for field in ("like_count", "comment_count", "view_count", "hashtag_count"):
        cleaned[field] = _safe_int(post.get(field), 0)

    cleaned["engagement_rate"] = _safe_float(post.get("engagement_rate"), 0.0)
    cleaned["timestamp"]       = _normalize_timestamp(post.get("timestamp"))
    cleaned["caption"]         = post.get("caption") or ""

    # Deduplicate hashtags
    raw_tags                       = post.get("hashtags", []) or []
    cleaned["hashtags"]            = _deduplicate_hashtags(raw_tags)
    cleaned["hashtag_count"]       = len(cleaned["hashtags"])

    # Caption without emoji (for NLP)
    cleaned["caption_clean"]       = _strip_emoji(cleaned["caption"])

    # Normalize media type to uppercase
    media_raw                      = str(post.get("media_type", "IMAGE")).upper()
    cleaned["media_type"]          = media_raw

    # Mentions — flatten to list of strings
    raw_mentions                   = post.get("mentions", []) or []
    cleaned["mentions"]            = [str(m).strip() for m in raw_mentions if m]

    return cleaned


def clean_profile(profile: dict) -> dict:
    """Stage 1: Normalize a raw profile record."""
    cleaned = dict(profile)
    for field in ("follower_count", "following_count", "post_count", "posts_scraped"):
        cleaned[field] = _safe_int(profile.get(field), 0)
    for field in ("engagement_rate", "follower_following_ratio",
                  "like_count_avg", "comment_count_avg", "view_count_avg",
                  "engagement_std", "follower_count_log"):
        cleaned[field] = _safe_float(profile.get(field), 0.0)
    cleaned["scraped_at"] = _normalize_timestamp(profile.get("scraped_at"))
    return cleaned


def clean_document(doc: dict) -> dict:
    """Apply cleaning to the full MongoDB-style document."""
    doc["profile"] = clean_profile(doc.get("profile", {}))
    doc["posts"]   = [clean_post(p) for p in doc.get("posts", [])]
    return doc


# ============================================================================
#  STAGE 2 (PART A) — POST-LEVEL: CONTENT & ENGAGEMENT FEATURES
# ============================================================================

def count_emojis(text: str) -> int:
    return len(EMOJI_PATTERN.findall(text))


def detect_promo_codes(text: str) -> list:
    return [m.group(0) for m in PROMO_CODE_PATTERN.finditer(text)]


def detect_affiliate_link(text: str) -> bool:
    return bool(AFFILIATE_LINK_PATTERN.search(text))


def compute_brand_keyword_score(caption: str, mentions: list) -> float:
    """
    Rough 0–1 score based on commercial signal density.
    Factors: #ad, 'link in bio', promo codes, affiliate URLs, mention count.
    """
    score = 0.0
    lower = caption.lower()

    for pat in SPONSORED_PATTERNS:
        if re.search(pat, lower):
            score += 0.2

    if detect_promo_codes(caption):
        score += 0.2

    if detect_affiliate_link(caption + " ".join(mentions)):
        score += 0.2

    mention_bonus = min(len(mentions) * 0.05, 0.2)
    score += mention_bonus

    return min(round(score, 4), 1.0)


def classify_collaboration(post: dict) -> dict:
    """
    Detect and classify collaboration signals at the post level.
    Returns a dict of collaboration features.
    """
    caption   = post.get("caption", "")
    mentions  = post.get("mentions", [])
    lower_cap = caption.lower()

    is_ad         = any(re.search(p, lower_cap) for p in SPONSORED_PATTERNS)
    promo_codes   = detect_promo_codes(caption)
    aff_link      = detect_affiliate_link(caption + " ".join(mentions))
    brand_kw      = compute_brand_keyword_score(caption, mentions)
    is_collab     = bool(is_ad or promo_codes or aff_link or brand_kw >= 0.4)

    collab_types  = post.get("collab_types", ["ORGANIC"])

    return {
        "is_collaboration":    is_collab,
        "mention_brand_count": len(mentions),
        "promo_code_present":  bool(promo_codes),
        "affiliate_link_present": aff_link,
        "brand_keyword_score": brand_kw,
        "collab_types":        collab_types,
    }


def extract_post_features(post: dict, follower_count: int) -> dict:
    """
    Stage 2 — Full post-level feature extraction.
    Returns a flat feature dict for this post.
    """
    caption  = post.get("caption", "")
    hashtags = post.get("hashtags", [])
    mentions = post.get("mentions", [])

    like_count    = _safe_int(post.get("like_count"))
    comment_count = _safe_int(post.get("comment_count"))
    view_count    = _safe_int(post.get("view_count"))
    engagement    = like_count + comment_count
    eng_rate      = engagement / follower_count if follower_count > 0 else 0.0

    caption_clean = _strip_emoji(caption)
    words         = caption_clean.split()
    word_count    = len(words)
    cap_length    = len(caption_clean)
    emoji_count   = count_emojis(caption)
    hashtag_count = len(hashtags)
    mention_count = len(mentions)
    hashtag_density = hashtag_count / cap_length if cap_length > 0 else 0.0

    media_type_str = str(post.get("media_type", "IMAGE")).upper()
    media_encoded  = MEDIA_TYPE_MAP.get(media_type_str, 0)

    collab_feats  = classify_collaboration(post)
    est_value     = _safe_float(post.get("estimated_value_usd"), 0.0)

    return {
        # Identifiers
        "post_id":               post.get("post_id"),
        "timestamp":             post.get("timestamp"),
        "media_type":            media_type_str,
        # Engagement
        "post_like_count":       like_count,
        "post_comment_count":    comment_count,
        "post_view_count":       view_count,
        "post_engagement":       engagement,
        "post_engagement_rate":  round(eng_rate, 6),
        # Content structure
        "hashtag_count":         hashtag_count,
        "mention_count":         mention_count,
        "caption_length":        cap_length,
        "emoji_count":           emoji_count,
        "word_count":            word_count,
        "hashtag_density":       round(hashtag_density, 6),
        # Media encoding
        "media_type_encoded":    media_encoded,
        # Collaboration
        **collab_feats,
        # Pricing
        "estimated_value_usd":   est_value,
    }


# ============================================================================
#  STAGE 3 — PROFILE-LEVEL AGGREGATION
# ============================================================================

def _mean(values: list) -> float:
    return statistics.mean(values) if values else 0.0


def _std(values: list) -> float:
    return statistics.stdev(values) if len(values) > 1 else 0.0


def _cv(values: list) -> float:
    """Coefficient of variation = std / mean."""
    m = _mean(values)
    return _std(values) / m if m > 0 else 0.0


def aggregate_profile_features(post_features: list, profile: dict) -> dict:
    """
    Stage 3 — Aggregate post-level features into profile-level metrics.
    """
    if not post_features:
        return {}

    likes         = [p["post_like_count"]     for p in post_features]
    comments      = [p["post_comment_count"]  for p in post_features]
    views         = [p["post_view_count"]      for p in post_features]
    eng_rates     = [p["post_engagement_rate"] for p in post_features]
    hashtag_cnts  = [p["hashtag_count"]        for p in post_features]
    cap_lengths   = [p["caption_length"]       for p in post_features]
    mention_cnts  = [p["mention_count"]        for p in post_features]
    hash_densities= [p["hashtag_density"]      for p in post_features]

    total_posts   = len(post_features)
    video_posts   = sum(1 for p in post_features if p["media_type"] == "VIDEO")
    image_posts   = sum(1 for p in post_features if p["media_type"] == "IMAGE")
    carousel_posts= sum(1 for p in post_features if p["media_type"] == "CAROUSEL")

    avg_eng       = _mean(eng_rates)

    return {
        # Engagement aggregations
        "avg_likes":             round(_mean(likes), 2),
        "avg_comments":          round(_mean(comments), 2),
        "avg_views":             round(_mean(views), 2),
        "avg_engagement_rate":   round(avg_eng, 6),
        "engagement_std":        round(_std(eng_rates), 6),
        "engagement_variance":   round(_std(eng_rates) ** 2, 6),
        "engagement_cv":         round(_cv(eng_rates), 6),
        # Content distribution
        "total_posts_analyzed":  total_posts,
        "video_count":           video_posts,
        "image_count":           image_posts,
        "carousel_count":        carousel_posts,
        "video_ratio":           round(video_posts / total_posts, 4),
        "image_ratio":           round(image_posts / total_posts, 4),
        "carousel_ratio":        round(carousel_posts / total_posts, 4),
        # Hashtag & caption metrics
        "avg_hashtag_count":     round(_mean(hashtag_cnts), 2),
        "hashtag_density_avg":   round(_mean(hash_densities), 6),
        "avg_caption_length":    round(_mean(cap_lengths), 2),
        "avg_mention_count":     round(_mean(mention_cnts), 2),
    }


# ============================================================================
#  STAGE 4 — TEMPORAL ACTIVITY FEATURES
# ============================================================================

def compute_temporal_features(post_features: list) -> dict:
    """
    Stage 4 — Compute posting frequency and consistency from timestamps.
    """
    timestamps = [
        p["timestamp"] for p in post_features
        if isinstance(p.get("timestamp"), datetime)
    ]

    if len(timestamps) < 2:
        return {
            "posting_frequency_weekly":  0.0,
            "posting_frequency_monthly": 0.0,
            "avg_days_between_posts":    0.0,
            "posting_std_dev_days":      0.0,
            "posting_consistency_score": 0.0,
        }

    timestamps_sorted = sorted(timestamps)
    gaps_days = [
        (timestamps_sorted[i + 1] - timestamps_sorted[i]).total_seconds() / 86400
        for i in range(len(timestamps_sorted) - 1)
    ]

    total_span_days = max(
        (timestamps_sorted[-1] - timestamps_sorted[0]).total_seconds() / 86400,
        1.0,
    )
    total_posts     = len(timestamps_sorted)
    weekly_freq     = (total_posts / total_span_days) * 7
    monthly_freq    = (total_posts / total_span_days) * 30
    avg_gap         = _mean(gaps_days)
    std_gap         = _std(gaps_days)

    # Consistency score: lower std relative to mean = more consistent (0–1)
    cv_gap   = std_gap / avg_gap if avg_gap > 0 else 1.0
    cons_score = max(0.0, round(1.0 - min(cv_gap, 1.0), 4))

    return {
        "posting_frequency_weekly":  round(weekly_freq, 4),
        "posting_frequency_monthly": round(monthly_freq, 4),
        "avg_days_between_posts":    round(avg_gap, 4),
        "posting_std_dev_days":      round(std_gap, 4),
        "posting_consistency_score": cons_score,
    }


# ============================================================================
#  STAGE 5 — AUDIENCE & GROWTH FEATURES
# ============================================================================

def compute_audience_features(profile: dict) -> dict:
    """
    Stage 5 — Follower-based influence signals.
    """
    followers = _safe_int(profile.get("follower_count"))
    following = _safe_int(profile.get("following_count"))
    ratio     = _safe_float(profile.get("follower_following_ratio"))
    log_f     = math.log(followers) if followers > 0 else 0.0

    return {
        "follower_count":            followers,
        "follower_count_log":        round(log_f, 4),
        "following_count":           following,
        "follower_following_ratio":  round(ratio, 4),
        "audience_size_score":       round(log_f, 4),   # alias for clarity
    }


# ============================================================================
#  STAGE 6 — CONTENT TOPIC FEATURES
# ============================================================================

def compute_topic_vector(post_features: list) -> dict:
    """
    Stage 6 — Extract content topic categories from hashtags and captions.
    Returns a binary topic vector and the dominant topic.
    """
    all_text = []
    for p in post_features:
        all_text.append(p.get("caption_clean", "").lower())

    combined = " ".join(all_text)
    tokens   = set(re.findall(r"\w+", combined))

    topic_scores = {}
    for topic, keywords in TOPIC_TAXONOMY.items():
        hits = sum(1 for kw in keywords if kw in tokens)
        topic_scores[topic] = hits

    # Binary encoding
    topic_vector = {f"topic_{t}": int(v > 0) for t, v in topic_scores.items()}

    # Dominant topic
    dominant = max(topic_scores, key=topic_scores.get) if any(topic_scores.values()) else "lifestyle"
    topic_vector["dominant_topic"] = dominant

    return topic_vector


# ============================================================================
#  STAGE 7 — COLLABORATION FEATURES
# ============================================================================

def compute_collaboration_features(post_features: list, profile_agg: dict) -> dict:
    """
    Stage 7 — Aggregate collaboration signals across all posts.
    """
    total           = len(post_features)
    collab_posts    = [p for p in post_features if p.get("is_collaboration")]
    aff_link_posts  = [p for p in post_features if p.get("affiliate_link_present")]
    promo_posts     = [p for p in post_features if p.get("promo_code_present")]
    sponsored_count = sum(
        1 for p in post_features
        if "ADVERTISEMENT" in p.get("collab_types", [])
        or "SPONSORED_POST" in p.get("collab_types", [])
    )

    collab_ratio    = len(collab_posts) / total if total > 0 else 0.0
    aff_ratio       = len(aff_link_posts) / total if total > 0 else 0.0
    avg_brand_kw    = _mean([p.get("brand_keyword_score", 0) for p in post_features])
    avg_mentions    = _mean([p.get("mention_brand_count", 0) for p in post_features])

    total_est_value = sum(p.get("estimated_value_usd", 0) for p in post_features)

    return {
        "collab_post_count":        len(collab_posts),
        "collab_post_ratio":        round(collab_ratio, 4),
        "affiliate_link_ratio":     round(aff_ratio, 4),
        "sponsored_post_count":     sponsored_count,
        "promo_code_post_count":    len(promo_posts),
        "brand_mentions_per_post":  round(avg_mentions, 4),
        "avg_brand_keyword_score":  round(avg_brand_kw, 4),
        "total_estimated_value_usd": round(total_est_value, 2),
    }


# ============================================================================
#  STAGE 8 — CREATOR AUTHORITY FEATURES
# ============================================================================

def compute_authority_features(
    audience_feats: dict,
    profile_agg: dict,
    temporal_feats: dict,
) -> dict:
    """
    Stage 8 — Composite influence scores used in marketing platforms.

    authority_score = 0.5 * log_followers
                    + 0.3 * engagement_rate (scaled 0–10)
                    + 0.2 * posting_frequency_weekly (capped at 10)
    """
    log_f        = audience_feats.get("follower_count_log", 0.0)
    eng_rate     = profile_agg.get("avg_engagement_rate", 0.0)
    post_freq    = temporal_feats.get("posting_frequency_weekly", 0.0)
    eng_std      = profile_agg.get("engagement_std", 0.0)
    eng_cv       = profile_agg.get("engagement_cv", 1.0)

    # Scale engagement rate to 0–10 (0.01 = good, 0.10 = excellent)
    eng_score    = min(eng_rate * 100, 10.0)
    freq_score   = min(post_freq, 10.0)

    authority_score = (
        0.5 * log_f
        + 0.3 * eng_score
        + 0.2 * freq_score
    )
    # Normalize to 0–100 (log(1B) ~ 20.7, so max raw ≈ 14.35)
    authority_score_normalized = round(min(authority_score / 14.35 * 100, 100.0), 2)

    # Content quality: penalized by high variance
    content_quality_score = round(
        max(0.0, eng_score * (1.0 - min(eng_cv, 1.0))), 4
    )

    # Engagement consistency: inverse CV
    consistency_score = temporal_feats.get("posting_consistency_score", 0.0)

    return {
        "authority_score":              authority_score_normalized,
        "content_quality_score":        content_quality_score,
        "engagement_consistency_score": consistency_score,
    }


# ============================================================================
#  STAGE 9 — BRAND RISK FEATURES
# ============================================================================

def compute_brand_risk_features(post_features: list) -> dict:
    """
    Stage 9 — Detect potentially brand-unsafe content signals.
    """
    total  = max(len(post_features), 1)

    def _score_for_category(category_keywords: list) -> float:
        hits = 0
        for p in post_features:
            text = (p.get("caption_clean", "") or "").lower()
            if any(kw in text for kw in category_keywords):
                hits += 1
        return round(hits / total, 4)

    controversial_score = _score_for_category(BRAND_RISK_KEYWORDS["controversial"])
    political_ratio     = _score_for_category(BRAND_RISK_KEYWORDS["political"])
    sensitive_ratio     = _score_for_category(BRAND_RISK_KEYWORDS["sensitive"])
    toxicity_score      = _score_for_category(BRAND_RISK_KEYWORDS["toxic"])

    composite_risk = (
        0.3 * controversial_score
        + 0.25 * political_ratio
        + 0.25 * sensitive_ratio
        + 0.2 * toxicity_score
    )

    if composite_risk < 0.05:
        risk_category = "LOW"
    elif composite_risk < 0.20:
        risk_category = "MEDIUM"
    else:
        risk_category = "HIGH"

    return {
        "controversial_keyword_score": controversial_score,
        "political_content_ratio":     political_ratio,
        "sensitive_topic_ratio":       sensitive_ratio,
        "toxicity_score":              toxicity_score,
        "composite_risk_score":        round(composite_risk, 4),
        "brand_risk_category":         risk_category,
    }


# ============================================================================
#  STAGE 10 — FINAL ML FEATURE VECTOR ASSEMBLY
# ============================================================================

def build_feature_vector(
    audience_feats:   dict,
    profile_agg:      dict,
    temporal_feats:   dict,
    collab_feats:     dict,
    authority_feats:  dict,
    risk_feats:       dict,
    topic_vector:     dict,
) -> dict:
    """
    Stage 10 — Assemble the final 30–45 dimension ML feature vector.
    Numeric features only; topic vector is one-hot encoded inline.
    """
    fv = {
        # ── Audience (5)
        "followers_log":              audience_feats.get("follower_count_log", 0.0),
        "follower_following_ratio":   audience_feats.get("follower_following_ratio", 0.0),
        "audience_size_score":        audience_feats.get("audience_size_score", 0.0),
        "follower_count":             audience_feats.get("follower_count", 0),
        "following_count":            audience_feats.get("following_count", 0),

        # ── Engagement (6)
        "engagement_rate_avg":        profile_agg.get("avg_engagement_rate", 0.0),
        "engagement_std":             profile_agg.get("engagement_std", 0.0),
        "engagement_variance":        profile_agg.get("engagement_variance", 0.0),
        "engagement_cv":              profile_agg.get("engagement_cv", 0.0),
        "avg_likes":                  profile_agg.get("avg_likes", 0.0),
        "avg_comments":               profile_agg.get("avg_comments", 0.0),
        "avg_views":                  profile_agg.get("avg_views", 0.0),

        # ── Content distribution (3)
        "video_ratio":                profile_agg.get("video_ratio", 0.0),
        "image_ratio":                profile_agg.get("image_ratio", 0.0),
        "carousel_ratio":             profile_agg.get("carousel_ratio", 0.0),

        # ── Caption / hashtag (4)
        "avg_hashtag_count":          profile_agg.get("avg_hashtag_count", 0.0),
        "hashtag_density_avg":        profile_agg.get("hashtag_density_avg", 0.0),
        "avg_caption_length":         profile_agg.get("avg_caption_length", 0.0),
        "avg_mention_count":          profile_agg.get("avg_mention_count", 0.0),

        # ── Temporal (4)
        "posting_frequency_weekly":   temporal_feats.get("posting_frequency_weekly", 0.0),
        "posting_frequency_monthly":  temporal_feats.get("posting_frequency_monthly", 0.0),
        "avg_days_between_posts":     temporal_feats.get("avg_days_between_posts", 0.0),
        "posting_std_dev_days":       temporal_feats.get("posting_std_dev_days", 0.0),

        # ── Collaboration (5)
        "collab_post_ratio":          collab_feats.get("collab_post_ratio", 0.0),
        "affiliate_link_ratio":       collab_feats.get("affiliate_link_ratio", 0.0),
        "sponsored_post_count":       collab_feats.get("sponsored_post_count", 0),
        "brand_mentions_per_post":    collab_feats.get("brand_mentions_per_post", 0.0),
        "avg_brand_keyword_score":    collab_feats.get("avg_brand_keyword_score", 0.0),

        # ── Authority (3)
        "authority_score":            authority_feats.get("authority_score", 0.0),
        "content_quality_score":      authority_feats.get("content_quality_score", 0.0),
        "engagement_consistency_score": authority_feats.get("engagement_consistency_score", 0.0),

        # ── Brand risk (4)
        "controversial_keyword_score":risk_feats.get("controversial_keyword_score", 0.0),
        "political_content_ratio":    risk_feats.get("political_content_ratio", 0.0),
        "sensitive_topic_ratio":      risk_feats.get("sensitive_topic_ratio", 0.0),
        "toxicity_score":             risk_feats.get("toxicity_score", 0.0),
    }

    # ── Topic one-hot (8)
    for topic in TOPIC_TAXONOMY:
        fv[f"topic_{topic}"] = topic_vector.get(f"topic_{topic}", 0)

    return fv


# ============================================================================
#  MASTER PIPELINE ENTRY POINT
# ============================================================================

def run_pipeline(raw_document: dict, strict_filter: bool = False) -> dict:
    """
    Full end-to-end pipeline.
    Accepts a raw MongoDB document and returns a fully enriched output dict.
    """
    # ── Stage 0: Eligibility
    doc = apply_eligibility_filter(raw_document, strict=strict_filter)

    if not doc["influencer_valid"]:
        return {
            "username":           doc.get("profile", {}).get("username", "unknown"),
            "influencer_valid":   False,
            "influencer_tier":    "none",
            "creator_type":       "NON_INFLUENCER",
            "paid_collab_eligible": False,
            "feature_vector":     None,
            "message":            "Account does not meet influencer eligibility criteria.",
        }

    # ── Stage 1: Data Cleaning
    doc = clean_document(doc)
    profile = doc["profile"]
    posts   = doc["posts"]
    followers = _safe_int(profile.get("follower_count"))

    # ── Stage 2: Post-level features
    post_features = [extract_post_features(p, followers) for p in posts]

    # ── Stage 3: Profile aggregation
    profile_agg = aggregate_profile_features(post_features, profile)

    # ── Stage 4: Temporal features
    temporal_feats = compute_temporal_features(post_features)

    # ── Stage 5: Audience features
    audience_feats = compute_audience_features(profile)

    # ── Stage 6: Topic vector
    topic_vector = compute_topic_vector(post_features)

    # ── Stage 7: Collaboration features
    collab_feats = compute_collaboration_features(post_features, profile_agg)

    # ── Stage 8: Authority features
    authority_feats = compute_authority_features(
        audience_feats, profile_agg, temporal_feats
    )

    # ── Stage 9: Brand risk features
    risk_feats = compute_brand_risk_features(post_features)

    # ── Stage 10: Final feature vector
    feature_vector = build_feature_vector(
        audience_feats,
        profile_agg,
        temporal_feats,
        collab_feats,
        authority_feats,
        risk_feats,
        topic_vector,
    )

    return {
        "username":             profile.get("username"),
        "influencer_valid":     doc["influencer_valid"],
        "influencer_tier":      doc["influencer_tier"],
        "creator_type":         doc["creator_type"],
        "paid_collab_eligible": doc["paid_collab_eligible"],
        # Intermediate stage outputs (useful for debugging)
        "stages": {
            "audience":      audience_feats,
            "profile_agg":   profile_agg,
            "temporal":      temporal_feats,
            "collab":        collab_feats,
            "authority":     authority_feats,
            "brand_risk":    risk_feats,
            "topic_vector":  topic_vector,
            "post_features": post_features,
        },
        # Final ML-ready vector
        "feature_vector": feature_vector,
        "feature_dim":    len(feature_vector),
    }


# ============================================================================
#  STAGE 11 — ML MODEL STUBS
# ============================================================================

class CollaborationPricePredictor:
    """
    XGBoost Regressor — predicts estimated_value_usd per post.
    Target: estimated_value_usd
    """

    def __init__(self):
        if not HAS_XGB:
            raise ImportError("xgboost is required. Install with: pip install xgboost")
        self.model = xgb.XGBRegressor(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            objective="reg:squarederror",
        )
        self._feature_names = None

    def fit(self, X, y, feature_names=None):
        self._feature_names = feature_names
        self.model.fit(X, y)
        return self

    def predict(self, X):
        return self.model.predict(X)

    def feature_importance(self) -> dict:
        if not hasattr(self.model, "feature_importances_"):
            return {}
        scores = self.model.feature_importances_
        names  = self._feature_names or [f"f{i}" for i in range(len(scores))]
        return dict(sorted(zip(names, scores), key=lambda x: -x[1]))


class BrandRiskClassifier:
    """
    RandomForestClassifier — predicts brand_risk_category (LOW / MEDIUM / HIGH).
    """

    LABELS = ["LOW", "MEDIUM", "HIGH"]

    def __init__(self):
        if not HAS_SKLEARN:
            raise ImportError("scikit-learn is required. Install with: pip install scikit-learn")
        self.model   = RandomForestClassifier(
            n_estimators=200,
            max_depth=8,
            random_state=42,
            class_weight="balanced",
        )
        self.encoder = LabelEncoder()
        self.encoder.fit(self.LABELS)

    def fit(self, X, y_labels):
        y_enc = self.encoder.transform(y_labels)
        self.model.fit(X, y_enc)
        return self

    def predict(self, X) -> list:
        y_enc = self.model.predict(X)
        return self.encoder.inverse_transform(y_enc).tolist()

    def predict_proba(self, X) -> list:
        proba = self.model.predict_proba(X)
        return [
            dict(zip(self.LABELS, row.tolist()))
            for row in proba
        ]


class CreatorPerformanceScorer:
    """
    Weighted scoring model — outputs creator_score in range 0–100.

    Weights:
        authority_score              40%
        avg_engagement_rate (scaled) 30%
        posting_consistency_score    15%
        collab_post_ratio            15%
    """

    WEIGHTS = {
        "authority_score":              0.40,
        "avg_engagement_rate":          0.30,  # will be scaled x100 and capped at 10
        "posting_consistency_score":    0.15,
        "collab_post_ratio":            0.15,
    }

    def score(self, feature_vector: dict) -> float:
        auth  = feature_vector.get("authority_score", 0.0)
        eng   = min(feature_vector.get("engagement_rate_avg", 0.0) * 100, 10.0) * 10
        cons  = feature_vector.get("engagement_consistency_score", 0.0) * 100
        collab= feature_vector.get("collab_post_ratio", 0.0) * 100

        raw = (
            self.WEIGHTS["authority_score"]           * auth
            + self.WEIGHTS["avg_engagement_rate"]     * eng
            + self.WEIGHTS["posting_consistency_score"] * cons
            + self.WEIGHTS["collab_post_ratio"]       * collab
        )
        return round(min(max(raw, 0.0), 100.0), 2)


# ============================================================================
#  STAGE 12 — MONGODB STORAGE HELPER
# ============================================================================

def store_features_to_mongodb(
    pipeline_output: dict,
    mongo_uri: str = "mongodb://localhost:27017",
    db_name: str   = "influencer_db",
    collection: str = "creator_features",
) -> bool:
    """
    Upsert the pipeline output into MongoDB collection `creator_features`.
    Document structure mirrors the spec's recommended schema.
    """
    if not HAS_MONGO:
        print("[WARN] pymongo not installed. Skipping MongoDB storage.")
        return False

    client = MongoClient(mongo_uri)
    db     = client[db_name]
    col    = db[collection]

    doc = {
        "username":           pipeline_output.get("username"),
        "features":           pipeline_output.get("feature_vector"),
        "tier":               pipeline_output.get("influencer_tier"),
        "influencer_valid":   pipeline_output.get("influencer_valid"),
        "creator_type":       pipeline_output.get("creator_type"),
        "brand_risk_category": (
            pipeline_output.get("stages", {})
            .get("brand_risk", {})
            .get("brand_risk_category", "UNKNOWN")
        ),
        "authority_score": (
            pipeline_output.get("stages", {})
            .get("authority", {})
            .get("authority_score", 0.0)
        ),
        "last_updated": datetime.utcnow(),
    }

    col.update_one(
        {"username": doc["username"]},
        {"$set": doc},
        upsert=True,
    )
    client.close()
    return True


# ============================================================================
#  MONGODB AGGREGATION FILTER (reference)
# ============================================================================
#
#  db.profiles.find({
#    "profile.follower_count":            { $gte: 1000 },
#    "profile.follower_following_ratio":  { $gte: 2    },
#    "profile.engagement_rate":           { $gte: 0.01 }
#  })
#
# ============================================================================


# ============================================================================
#  DEMO — run with sample data when executed directly
# ============================================================================

if __name__ == "__main__":
    import json

    # ── Sample: vinu_raut09 (should be rejected)
    vinu_doc = {
        "profile": {
            "username": "vinu_raut09",
            "follower_count": 890,
            "following_count": 704,
            "post_count": 13,
            "follower_following_ratio": 1.264,
            "engagement_rate": 0.337079,
            "posts_scraped": 8,
        },
        "posts": [],
    }

    # ── Sample: cristiano (should pass as MEGA)
    cristiano_doc = {
        "profile": {
            "username": "cristiano",
            "follower_count": 672022038,
            "following_count": 629,
            "post_count": 4018,
            "follower_following_ratio": 1068397.517,
            "engagement_rate": 0.006121,
            "posts_scraped": 12,
            "like_count_avg": 4057797.33,
            "comment_count_avg": 55799.5,
            "view_count_avg": 2650806.33,
            "engagement_std": 2086681.02,
        },
        "posts": [
            {
                "post_id": "DVUVYxwAOOz",
                "timestamp": "2026-03-04 07:50:23",
                "media_type": "image",
                "like_count": 1318870,
                "comment_count": 12452,
                "view_count": 0,
                "hashtag_count": 0,
                "hashtags": [],
                "caption": "We keep growing together! Important win!",
                "mentions": [],
                "promo_codes": [],
                "is_collaboration": False,
                "collab_types": ["ORGANIC"],
                "estimated_value_usd": 0,
            },
            {
                "post_id": "DU9MfenCJIs",
                "timestamp": "2026-02-20 07:50:23",
                "media_type": "video",
                "like_count": 2091612,
                "comment_count": 20341,
                "view_count": 13003763,
                "hashtag_count": 0,
                "hashtags": [],
                "caption": (
                    "A new chapter for me and @herbalife. "
                    "The next era of wellness is Pro2col. "
                    "Find out more - link in bio. #ad"
                ),
                "mentions": ["herbalife", "herbalifeceo"],
                "promo_codes": [],
                "is_collaboration": True,
                "collab_types": ["AFFILIATE_LINK"],
                "estimated_value_usd": 1344044.08,
            },
        ],
    }

    print("=" * 60)
    print("  PIPELINE DEMO")
    print("=" * 60)

    for label, doc in [("vinu_raut09", vinu_doc), ("cristiano", cristiano_doc)]:
        result = run_pipeline(doc)
        print(f"\n── {label} ──")
        print(f"  valid        : {result['influencer_valid']}")
        print(f"  tier         : {result['influencer_tier']}")
        print(f"  creator_type : {result['creator_type']}")
        if result["feature_vector"]:
            fv = result["feature_vector"]
            print(f"  feature_dim  : {result['feature_dim']}")
            print(f"  authority    : {result['stages']['authority']['authority_score']}")
            print(f"  risk         : {result['stages']['brand_risk']['brand_risk_category']}")
            print(f"  collab_ratio : {fv.get('collab_post_ratio')}")
            print(f"  dominant_topic: {result['stages']['topic_vector']['dominant_topic']}")

            scorer = CreatorPerformanceScorer()
            print(f"  creator_score: {scorer.score(fv)}")
        else:
            print(f"  [{result.get('message')}]")
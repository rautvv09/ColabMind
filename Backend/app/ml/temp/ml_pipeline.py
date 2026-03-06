"""
================================================================================
  Influencer ML Pipeline  —  Price Prediction, Risk Classification, Scoring
  Data Source : MongoDB Atlas  →  instagram_db.creator_features
  Currency    : INR (1 USD = 83.5 INR, override via USD_TO_INR env var)
  Training    : pandas DataFrame throughout — NO raw numpy in model.fit()
================================================================================

  INSTALL:
    pip install "pymongo[srv]" scikit-learn xgboost joblib pandas numpy

  USAGE:
    python ml_pipeline.py               → train all 3 models (Atlas + synthetic fallback)
    python ml_pipeline.py --synthetic   → train on synthetic data only (no Atlas)
    python ml_pipeline.py --evaluate    → print metrics from saved training_report.json

  OUTPUT → ./models/
    price_model.joblib      price_scaler.joblib
    risk_model.joblib       risk_encoder.joblib
    scorer_model.joblib     training_report.json
================================================================================
"""

import os, sys, json, math, warnings
import joblib
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

from sklearn.model_selection  import train_test_split, cross_val_score
from sklearn.preprocessing    import StandardScaler, LabelEncoder
from sklearn.metrics          import (
    mean_absolute_error, mean_squared_error, r2_score,
    classification_report, confusion_matrix, accuracy_score,
)
from sklearn.ensemble         import RandomForestClassifier
import xgboost as xgb
from pymongo import MongoClient

warnings.filterwarnings("ignore")

# ============================================================================
#  CONFIG
# ============================================================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://<USERNAME>:<PASSWORD>@<CLUSTER>.mongodb.net/?retryWrites=true&w=majority"
)
DB_NAME             = "instagram_db"
FEATURES_COLLECTION = "creator_features"
MODELS_DIR          = Path("./models")
MODELS_DIR.mkdir(exist_ok=True)

USD_TO_INR  = float(os.getenv("USD_TO_INR", "83.5"))
RISK_LABELS = ["LOW", "MEDIUM", "HIGH"]
TIER_LABELS = ["nano", "micro", "mid", "macro", "mega"]

# ── Feature column lists (must match feature_engineering_pipeline output) ───
PRICE_FEATURES = [
    "followers_log", "follower_following_ratio",
    "engagement_rate_avg", "engagement_cv",
    "avg_likes", "avg_comments", "avg_views",
    "posting_frequency_weekly", "video_ratio", "image_ratio",
    "avg_hashtag_count", "avg_caption_length", "avg_mention_count",
    "collab_post_ratio", "affiliate_link_ratio",
    "brand_mentions_per_post", "avg_brand_keyword_score",
    "authority_score", "content_quality_score",
    "engagement_consistency_score",
    "topic_fitness", "topic_travel", "topic_food", "topic_fashion",
    "topic_tech", "topic_comedy", "topic_sports", "topic_lifestyle",
]

RISK_FEATURES = [
    "followers_log", "engagement_rate_avg",
    "controversial_keyword_score", "political_content_ratio",
    "sensitive_topic_ratio", "toxicity_score",
    "collab_post_ratio", "avg_hashtag_count",
    "topic_fitness", "topic_travel", "topic_food", "topic_fashion",
    "topic_tech", "topic_comedy", "topic_sports", "topic_lifestyle",
]

SCORER_FEATURES = [
    "followers_log", "engagement_rate_avg", "engagement_cv",
    "posting_frequency_weekly", "posting_consistency_score",
    "video_ratio", "collab_post_ratio",
    "authority_score", "content_quality_score",
]


# ============================================================================
#  HELPERS
# ============================================================================

def format_inr(amount: float) -> str:
    """Format float as Indian currency string."""
    if amount >= 1_00_00_000: return f"₹{amount / 1_00_00_000:.2f} Cr"
    if amount >= 1_00_000:    return f"₹{amount / 1_00_000:.2f} L"
    if amount >= 1_000:       return f"₹{amount / 1_000:.2f} K"
    return f"₹{amount:.0f}"


def derive_price_inr(followers: int, eng_rate: float) -> float:
    """
    Indian market CPM-based price derivation.
    CPM (₹ per 1000 followers) × engagement multiplier (1× – 4×).
    """
    if followers <= 0:
        return 500.0
    cpm = (
        50  if followers < 10_000 else
        80  if followers < 100_000 else
        150 if followers < 1_000_000 else
        300 if followers < 10_000_000 else 500
    )
    base = (followers / 1000) * cpm
    mult = 1.0 + min(eng_rate * 10, 3.0)
    noise = np.random.uniform(0.90, 1.10)
    return round(base * mult * noise, 2)


def build_feature_df(df: pd.DataFrame, feature_cols: list) -> pd.DataFrame:
    """
    Extract feature columns from df as a clean pandas DataFrame.
    Missing columns are zero-filled.  NaN is filled with 0.
    Returns a DataFrame — model.fit() receives a DataFrame, never a numpy array.
    """
    result = pd.DataFrame(index=df.index)
    for col in feature_cols:
        result[col] = df[col].astype(float) if col in df.columns else 0.0
    return result.fillna(0.0)


def tier_context(tier: str, price_inr: float) -> dict:
    """Return Indian market benchmark range for a given tier."""
    benchmarks = {
        "nano":  (500,       5_000),
        "micro": (5_000,     50_000),
        "mid":   (50_000,    3_00_000),
        "macro": (3_00_000,  15_00_000),
        "mega":  (15_00_000, 5_00_00_000),
    }
    lo, hi = benchmarks.get(tier, (500, 5_000))
    pos = (
        "Within range" if lo <= price_inr <= hi else
        "Above range"  if price_inr > hi else
        "Below range"
    )
    return {
        "range":       f"{format_inr(lo)} – {format_inr(hi)}",
        "positioning": pos,
    }


# ============================================================================
#  ATLAS CONNECTION
# ============================================================================

def get_db():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    print(f"[✓] Connected  →  {DB_NAME}.{FEATURES_COLLECTION}")
    return client, client[DB_NAME]


# ============================================================================
#  DATA LOADING
# ============================================================================

def load_atlas_data(db) -> pd.DataFrame:
    """
    Load creator_features from Atlas and return a pandas DataFrame.
    Each row = one influencer.  price_inr is derived if not already present.
    """
    docs = list(db[FEATURES_COLLECTION].find({"influencer_valid": True}, {"_id": 0}))
    if not docs:
        raise ValueError(
            "No documents in creator_features. Run atlas_pipeline_runner.py first."
        )

    rows = []
    for doc in docs:
        fv = doc.get("feature_vector")
        if not fv:
            continue

        row = dict(fv)                                        # feature_vector dict
        row["username"]            = doc.get("username")
        row["influencer_tier"]     = doc.get("influencer_tier", "nano")
        row["brand_risk_category"] = doc.get("brand_risk_category", "LOW")
        row["creator_score"]       = float(doc.get("creator_score", 0.0))

        # ── Price target
        usd = float(fv.get("total_estimated_value_usd", 0.0))
        if usd > 0:
            row["price_inr"] = usd * USD_TO_INR
        else:
            followers = int(fv.get("follower_count", 0))
            eng_rate  = float(fv.get("engagement_rate_avg", 0.001))
            row["price_inr"] = derive_price_inr(followers, eng_rate)

        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"[✓] Loaded {len(df)} valid profiles from Atlas")
    return df


def generate_synthetic(n: int = 1500) -> pd.DataFrame:
    """
    Generate synthetic influencer profiles calibrated to the Indian market.
    Returns a pandas DataFrame (no raw numpy in final output).
    """
    np.random.seed(42)
    topics = [
        "fitness", "travel", "food", "fashion",
        "tech", "comedy", "sports", "lifestyle",
    ]

    tier_cfg = {
        # tier: (followers_lo, followers_hi, eng_lo, eng_hi, weight)
        "nano":  (1_000,      10_000,      0.03, 0.15, 0.45),
        "micro": (10_000,     100_000,     0.02, 0.08, 0.30),
        "mid":   (100_000,    1_000_000,   0.01, 0.05, 0.15),
        "macro": (1_000_000,  10_000_000,  0.005, 0.02, 0.07),
        "mega":  (10_000_000, 500_000_000, 0.001, 0.01, 0.03),
    }
    tiers   = list(tier_cfg.keys())
    weights = [v[4] for v in tier_cfg.values()]

    rows = []
    for i in range(n):
        tier = np.random.choice(tiers, p=weights)
        f_lo, f_hi, e_lo, e_hi, _ = tier_cfg[tier]

        followers = int(np.random.uniform(f_lo, f_hi))
        eng_rate  = round(float(np.random.uniform(e_lo, e_hi)), 6)
        log_f     = math.log(followers)
        price_inr = derive_price_inr(followers, eng_rate)
        risk      = np.random.choice(RISK_LABELS, p=[0.70, 0.22, 0.08])
        topic_idx = int(np.random.randint(0, 8))
        topic_vec = {f"topic_{t}": int(j == topic_idx) for j, t in enumerate(topics)}

        authority = min(
            (0.5 * log_f + 0.3 * min(eng_rate * 100, 10) + 0.2 * float(np.random.uniform(0, 10)))
            / 14.35 * 100,
            100.0,
        )
        c_score = min(
            0.40 * authority
            + 0.30 * min(eng_rate * 1000, 10) * 10
            + 0.15 * float(np.random.uniform(0, 100))
            + 0.15 * float(np.random.uniform(0, 100)),
            100.0,
        )

        row = {
            "username":                     f"synth_{i}",
            "influencer_tier":              tier,
            "brand_risk_category":          risk,
            "creator_score":                round(c_score, 2),
            "price_inr":                    round(price_inr, 2),
            # ── Audience
            "followers_log":                round(log_f, 4),
            "follower_count":               followers,
            "follower_following_ratio":     round(float(np.random.uniform(2, 1000)), 2),
            "following_count":              int(followers / float(np.random.uniform(2, 100))),
            # ── Engagement
            "engagement_rate_avg":          eng_rate,
            "engagement_std":               round(eng_rate * float(np.random.uniform(0.1, 0.5)), 6),
            "engagement_cv":                round(float(np.random.uniform(0.1, 0.8)), 4),
            "avg_likes":                    round(followers * eng_rate * 0.9, 2),
            "avg_comments":                 round(followers * eng_rate * 0.1, 2),
            "avg_views":                    round(followers * float(np.random.uniform(0.5, 2.0)), 2),
            # ── Temporal
            "posting_frequency_weekly":     round(float(np.random.uniform(0.5, 14)), 2),
            "posting_consistency_score":    round(float(np.random.uniform(0.3, 1.0)), 4),
            # ── Content
            "video_ratio":                  round(float(np.random.uniform(0.1, 0.9)), 4),
            "image_ratio":                  round(float(np.random.uniform(0.1, 0.9)), 4),
            "carousel_ratio":               round(float(np.random.uniform(0.0, 0.3)), 4),
            "avg_hashtag_count":            round(float(np.random.uniform(0, 30)), 2),
            "avg_caption_length":           round(float(np.random.uniform(10, 300)), 2),
            "avg_mention_count":            round(float(np.random.uniform(0, 5)), 2),
            "hashtag_density_avg":          round(float(np.random.uniform(0, 0.5)), 6),
            # ── Collaboration
            "collab_post_ratio":            round(float(np.random.uniform(0, 0.3)), 4),
            "affiliate_link_ratio":         round(float(np.random.uniform(0, 0.2)), 4),
            "sponsored_post_count":         int(np.random.randint(0, 10)),
            "brand_mentions_per_post":      round(float(np.random.uniform(0, 3)), 4),
            "avg_brand_keyword_score":      round(float(np.random.uniform(0, 0.5)), 4),
            # ── Authority
            "authority_score":              round(authority, 2),
            "content_quality_score":        round(float(np.random.uniform(0, 5)), 4),
            "engagement_consistency_score": round(float(np.random.uniform(0.2, 1.0)), 4),
            # ── Risk signals
            "controversial_keyword_score":  round(float(np.random.uniform(0, 0.1)), 4),
            "political_content_ratio":      round(float(np.random.uniform(0, 0.1)), 4),
            "sensitive_topic_ratio":        round(float(np.random.uniform(0, 0.1)), 4),
            "toxicity_score":               round(float(np.random.uniform(0, 0.05)), 4),
            **topic_vec,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"[✓] Generated {n} synthetic profiles")
    return df


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """Impute, clip, and log-transform the price target column."""
    # Ensure all numeric columns are float
    for col in df.select_dtypes(include=[np.number]).columns:
        df[col] = df[col].astype(float).fillna(0.0)

    # Cap extreme price outliers at 99th percentile
    p99 = float(df["price_inr"].quantile(0.99))
    df["price_inr"] = df["price_inr"].clip(upper=p99)

    # Log-transform price (reduces right skew for regression)
    df["price_inr_log"] = np.log1p(df["price_inr"])
    return df


# ============================================================================
#  MODEL 1 — PRICE PREDICTION  (XGBoost, pandas DataFrame input)
# ============================================================================

def train_price_model(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 62)
    print("  MODEL 1  —  PRICE PREDICTION  (XGBoost Regressor)")
    print("  Target   :  price per sponsored post in INR")
    print("=" * 62)

    # ── Build feature DataFrame and target Series
    X: pd.DataFrame = build_feature_df(df, PRICE_FEATURES)
    y: pd.Series    = df["price_inr_log"].astype(float)

    # Drop rows where price is zero (uninformative)
    mask = y > 0
    X, y = X[mask].reset_index(drop=True), y[mask].reset_index(drop=True)
    print(f"  Training samples : {len(X)}")

    # ── Train/test split — still DataFrames
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Scale (fit on DataFrame, transform returns DataFrame)
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train), columns=PRICE_FEATURES, index=X_train.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test), columns=PRICE_FEATURES, index=X_test.index
    )

    # ── XGBoost receives a pandas DataFrame directly
    model = xgb.XGBRegressor(
        n_estimators=500, max_depth=6, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        reg_alpha=0.1, reg_lambda=1.0, random_state=42,
        objective="reg:squarederror", verbosity=0,
        enable_categorical=False,
    )
    model.fit(
        X_train_scaled, y_train,
        eval_set=[(X_test_scaled, y_test)],
        verbose=False,
    )

    # ── Evaluate — inverse log-transform back to INR
    y_pred_log: pd.Series = pd.Series(model.predict(X_test_scaled), index=y_test.index)
    y_pred_inr = np.expm1(y_pred_log)
    y_true_inr = np.expm1(y_test)

    mae  = mean_absolute_error(y_true_inr, y_pred_inr)
    rmse = math.sqrt(mean_squared_error(y_true_inr, y_pred_inr))
    r2   = r2_score(y_true_inr, y_pred_inr)
    mape = float(np.mean(np.abs((y_true_inr - y_pred_inr) / y_true_inr.clip(lower=1))) * 100)

    print(f"  MAE       : {format_inr(mae)}")
    print(f"  RMSE      : {format_inr(rmse)}")
    print(f"  R²        : {r2:.4f}")
    print(f"  MAPE      : {mape:.2f}%")

    # ── 5-Fold Cross-Validation (also receives DataFrame)
    X_all_scaled = pd.DataFrame(
        scaler.transform(X), columns=PRICE_FEATURES, index=X.index
    )
    cv_model = xgb.XGBRegressor(
        n_estimators=200, max_depth=6, random_state=42, verbosity=0
    )
    cv_scores = cross_val_score(cv_model, X_all_scaled, y, cv=5, scoring="r2")
    print(f"  5-Fold CV R² : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")

    # ── Feature importance (from DataFrame column names)
    importance = dict(sorted(
        zip(X_train_scaled.columns, model.feature_importances_),
        key=lambda x: -x[1]
    ))
    print("\n  Top 10 Features:")
    for feat, score in list(importance.items())[:10]:
        bar = "█" * int(score * 250)
        print(f"    {feat:<42} {score:.4f}  {bar}")

    # ── Sample predictions
    print(f"\n  Sample Predictions (first 5 test rows):")
    print(f"    {'Actual':>15}   {'Predicted':>15}   {'Diff':>12}")
    for a, p in zip(y_true_inr.values[:5], y_pred_inr.values[:5]):
        diff, sign = p - a, "+"
        if diff < 0: sign = "-"; diff = abs(diff)
        print(f"    {format_inr(a):>15}   {format_inr(p):>15}   {sign}{format_inr(diff):>12}")

    # ── Save
    joblib.dump(model,  MODELS_DIR / "price_model.joblib")
    joblib.dump(scaler, MODELS_DIR / "price_scaler.joblib")
    print(f"\n  [✓] Saved → models/price_model.joblib")
    print(f"  [✓] Saved → models/price_scaler.joblib")

    return {
        "model": model, "scaler": scaler,
        "metrics": {"MAE_INR": mae, "RMSE_INR": rmse, "R2": r2, "MAPE_%": mape},
        "cv_r2_mean": float(cv_scores.mean()),
        "importance": {k: float(v) for k, v in importance.items()},
    }


# ============================================================================
#  MODEL 2 — BRAND RISK CLASSIFICATION  (RandomForest, pandas DataFrame input)
# ============================================================================

def train_risk_model(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 62)
    print("  MODEL 2  —  BRAND RISK CLASSIFIER  (RandomForest)")
    print("  Target   :  LOW / MEDIUM / HIGH")
    print("=" * 62)

    # ── Feature DataFrame
    X: pd.DataFrame = build_feature_df(df, RISK_FEATURES)

    # ── Label encode target — keep as pandas Series
    le = LabelEncoder()
    le.fit(RISK_LABELS)
    y: pd.Series = pd.Series(
        le.transform(df["brand_risk_category"].fillna("LOW")),
        name="brand_risk_encoded",
        index=df.index,
    )

    print(f"  Samples : {len(X)}")
    for cls, cnt in y.value_counts().sort_index().items():
        print(f"    {le.inverse_transform([cls])[0]:<8} : {cnt}")

    # ── Split — DataFrames preserved
    stratify = y if y.nunique() > 1 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=stratify
    )

    # ── RandomForest receives DataFrame directly
    model = RandomForestClassifier(
        n_estimators=300, max_depth=10, min_samples_split=4,
        class_weight="balanced", random_state=42, n_jobs=-1,
    )
    model.fit(X_train, y_train)

    # ── Evaluate
    y_pred = pd.Series(model.predict(X_test), index=y_test.index)
    acc    = accuracy_score(y_test, y_pred)
    labels = le.inverse_transform(sorted(y.unique()))

    print(f"\n  Accuracy : {acc:.4f}")
    print("\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=labels))

    cm = confusion_matrix(y_test, y_pred)
    print("  Confusion Matrix  (rows=Actual, cols=Predicted):")
    print("            " + "  ".join(f"{l:>8}" for l in labels))
    for i, row in enumerate(cm):
        print(f"  {labels[i]:>8}  " + "  ".join(f"{v:>8}" for v in row))

    # ── Feature importance
    importance = dict(sorted(
        zip(X_train.columns, model.feature_importances_),
        key=lambda x: -x[1]
    ))
    print("\n  Top 8 Features:")
    for feat, score in list(importance.items())[:8]:
        bar = "█" * int(score * 300)
        print(f"    {feat:<42} {score:.4f}  {bar}")

    joblib.dump(model, MODELS_DIR / "risk_model.joblib")
    joblib.dump(le,    MODELS_DIR / "risk_encoder.joblib")
    print(f"\n  [✓] Saved → models/risk_model.joblib")
    print(f"  [✓] Saved → models/risk_encoder.joblib")

    return {
        "model": model, "encoder": le,
        "metrics": {"accuracy": float(acc)},
        "importance": {k: float(v) for k, v in importance.items()},
    }


# ============================================================================
#  MODEL 3 — CREATOR SCORER  (XGBoost, pandas DataFrame input)
# ============================================================================

def train_scorer_model(df: pd.DataFrame) -> dict:
    print("\n" + "=" * 62)
    print("  MODEL 3  —  CREATOR PERFORMANCE SCORER  (XGBoost)")
    print("  Target   :  creator_score  0 – 100")
    print("=" * 62)

    # ── Feature DataFrame (only columns present in df)
    available = [c for c in SCORER_FEATURES if c in df.columns]
    X: pd.DataFrame = df[available].astype(float).fillna(0.0)
    y: pd.Series    = df["creator_score"].astype(float).clip(0.0, 100.0)

    print(f"  Samples  : {len(X)}")
    print(f"  Features : {available}")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── XGBoost receives DataFrame directly
    model = xgb.XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, random_state=42,
        objective="reg:squarederror", verbosity=0,
    )
    model.fit(X_train, y_train)

    y_pred: pd.Series = pd.Series(
        np.clip(model.predict(X_test), 0, 100),
        index=y_test.index
    )
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    print(f"  MAE  : {mae:.2f} pts")
    print(f"  R²   : {r2:.4f}")

    # ── Feature importance
    importance = dict(sorted(
        zip(X_train.columns, model.feature_importances_),
        key=lambda x: -x[1]
    ))
    print("\n  Feature Importance:")
    for feat, score in importance.items():
        bar = "█" * int(score * 300)
        print(f"    {feat:<42} {score:.4f}  {bar}")

    # ── Score distribution
    buckets = {"D  (0–40)": 0, "C (40–55)": 0, "B (55–70)": 0, "A (70–85)": 0, "S  (85+)": 0}
    for s in y_pred:
        if   s < 40:  buckets["D  (0–40)"]  += 1
        elif s < 55:  buckets["C (40–55)"] += 1
        elif s < 70:  buckets["B (55–70)"] += 1
        elif s < 85:  buckets["A (70–85)"] += 1
        else:         buckets["S  (85+)"]  += 1
    print("\n  Score Distribution (test set):")
    for grade, cnt in buckets.items():
        print(f"    {grade} : {cnt:>4}  {'█' * cnt}")

    joblib.dump(model, MODELS_DIR / "scorer_model.joblib")
    print(f"\n  [✓] Saved → models/scorer_model.joblib")

    return {
        "model": model, "features": available,
        "metrics": {"MAE": float(mae), "R2": float(r2)},
        "importance": {k: float(v) for k, v in importance.items()},
    }


# ============================================================================
#  SAVE TRAINING REPORT
# ============================================================================

def save_report(price_r: dict, risk_r: dict, scorer_r: dict, df: pd.DataFrame) -> None:
    report = {
        "trained_at":       datetime.utcnow().isoformat(),
        "training_samples": len(df),
        "usd_to_inr":       USD_TO_INR,
        "price_model": {
            "algorithm":  "XGBoost Regressor",
            "target":     "price_inr per sponsored post",
            "features":   PRICE_FEATURES,
            "metrics":    price_r["metrics"],
            "cv_r2":      price_r["cv_r2_mean"],
            "top_features": dict(list(price_r["importance"].items())[:10]),
        },
        "risk_model": {
            "algorithm": "RandomForest Classifier",
            "classes":   RISK_LABELS,
            "features":  RISK_FEATURES,
            "metrics":   risk_r["metrics"],
        },
        "scorer_model": {
            "algorithm": "XGBoost Regressor",
            "target":    "creator_score 0–100",
            "features":  scorer_r["features"],
            "metrics":   scorer_r["metrics"],
        },
    }
    with open(MODELS_DIR / "training_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  [✓] Saved → models/training_report.json")


# ============================================================================
#  EVALUATE — print saved report
# ============================================================================

def evaluate_saved() -> None:
    path = MODELS_DIR / "training_report.json"
    if not path.exists():
        print("[!] No training_report.json — run training first.")
        return
    with open(path) as f:
        r = json.load(f)
    sep = "=" * 62
    print(f"\n{sep}\n  SAVED MODEL EVALUATION REPORT\n{sep}")
    print(f"  Trained at  : {r['trained_at']}")
    print(f"  Samples     : {r['training_samples']}")
    print(f"  USD → INR   : {r['usd_to_inr']}")
    pm = r["price_model"]
    print(f"\n  ── Price Model  ({pm['algorithm']})")
    print(f"     MAE    : {format_inr(pm['metrics']['MAE_INR'])}")
    print(f"     RMSE   : {format_inr(pm['metrics']['RMSE_INR'])}")
    print(f"     R²     : {pm['metrics']['R2']:.4f}")
    print(f"     MAPE   : {pm['metrics']['MAPE_%']:.2f}%")
    print(f"     CV R²  : {pm['cv_r2']:.4f}")
    rm = r["risk_model"]
    print(f"\n  ── Risk Model  ({rm['algorithm']})")
    print(f"     Accuracy : {rm['metrics']['accuracy']:.4f}")
    sm = r["scorer_model"]
    print(f"\n  ── Scorer Model  ({sm['algorithm']})")
    print(f"     MAE  : {sm['metrics']['MAE']:.2f} pts")
    print(f"     R²   : {sm['metrics']['R2']:.4f}")
    print(sep)


# ============================================================================
#  MAIN TRAINING FLOW
# ============================================================================

def train_all(source: str = "atlas") -> None:
    print("\n" + "=" * 62)
    print("  INFLUENCER ML PIPELINE  —  TRAIN ALL 3 MODELS")
    print(f"  Currency : INR  (1 USD = ₹{USD_TO_INR})")
    print("=" * 62)

    df = pd.DataFrame()

    if source == "atlas":
        try:
            client, db = get_db()
            df = load_atlas_data(db)
            client.close()
            df = prepare_df(df)
        except Exception as e:
            print(f"[!] Atlas load failed: {e}")

    if len(df) < 50:
        print(f"\n[!] Only {len(df)} real samples — augmenting with 1500 synthetic profiles")
        synth = generate_synthetic(1500)
        df    = pd.concat([df, synth], ignore_index=True) if len(df) > 0 else synth

    df = prepare_df(df)
    print(f"\n[→] Total training profiles : {len(df)}")
    print(f"    Columns              : {len(df.columns)}")
    print(f"    Price range (INR)    : {format_inr(df['price_inr'].min())} – {format_inr(df['price_inr'].max())}")

    price_r  = train_price_model(df)
    risk_r   = train_risk_model(df)
    scorer_r = train_scorer_model(df)
    save_report(price_r, risk_r, scorer_r, df)

    print("\n" + "=" * 62)
    print("  ✓  ALL MODELS TRAINED & SAVED  →  ./models/")
    print("=" * 62)
    for f in sorted(MODELS_DIR.iterdir()):
        print(f"    {f.name:<38}  {f.stat().st_size / 1024:.1f} KB")


# ============================================================================
#  ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    args = sys.argv[1:]

    if not args:
        train_all(source="atlas")
    elif args[0] == "--synthetic":
        train_all(source="synthetic")
    elif args[0] == "--evaluate":
        evaluate_saved()
    else:
        print(__doc__)
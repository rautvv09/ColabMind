<div align="center">

<br/>

```
                              ██████╗ ██████╗ ██╗     ██╗      █████╗ ██████╗      █████╗ ██╗
                             ██╔════╝██╔═══██╗██║     ██║     ██╔══██╗██╔══██╗    ██╔══██╗██║
                             ██║     ██║   ██║██║     ██║     ███████║██████╔╝    ███████║██║
                             ██║     ██║   ██║██║     ██║     ██╔══██║██╔══██╗    ██╔══██║██║
                             ╚██████╗╚██████╔╝███████╗███████╗██║  ██║██████╔╝    ██║  ██║██║
                              ╚═════╝ ╚═════╝ ╚══════╝╚══════╝╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═╝╚═╝
```

**AI-Powered Instagram Creator Analytics & Brand Collaboration Platform**

<br/>

---
Live Demo : https://colabmind1.vercel.app/
---

[![React](https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white)](https://www.mongodb.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Vite](https://img.shields.io/badge/Vite-7-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org)

<br/>

> *Find the right creator. Predict the right price. Eliminate the risk.*

<br/>

</div>

---

## ✦ What is CollabAI?

**CollabAI** is a full-stack intelligence platform built for brands and marketers who collaborate with Instagram influencers. It eliminates the guesswork from influencer marketing by combining real-time Instagram scraping, a three-model ML pipeline, and an analytics-first dashboard into one cohesive product.

Search any Instagram creator → get their live stats → run AI predictions for **price**, **risk**, and **creator score** → create and track collaborations. All in one flow.

---

## ⚡ Core Features

| Module | What it does |
|---|---|
| 🔍 **Creator Search** | Smart lookup by Instagram handle. Hits DB first; auto-scrapes via SearchAPI if profile is new. Returns fresh stats in seconds. |
| 📊 **Creator Profile** | Full profile view — followers, engagement rate, avg likes/comments/views, post frequency, video ratio, and more. |
| 📈 **Analytics Dashboard** | Per-creator visual analytics: follower growth, engagement trends, content type breakdown via Chart.js. |
| 💰 **Price Predictor** | ML model predicts a fair collaboration price + ±15% price band based on 11 engineered features. |
| ⚠️ **Risk Assessment** | Classifies creator collaboration risk as Low / Medium / High with probability scores. |
| 🏆 **Creator Score** | Composite 0–10 score computed by a trained model; written back to MongoDB for persistence. |
| 🤝 **Collaboration Manager** | Create, view, and track brand ↔ creator deals. Stores agreed price, status, and timeline. |

---

## 🏗️ Architecture


<img width="1536" height="1024" alt="ApiFlow" src="https://github.com/user-attachments/assets/3f1f90e0-95a2-4ea1-a173-e567b4267faf" />

---

## 🤖 ML Models

Three independent models trained on scraped Instagram data and served via Flask:

### 1 · Price Prediction Model
> `POST /api/ai/price/predict`

Predicts a fair market price (in ₹) for a sponsored post, plus a ±15% confidence band.

**Input features:**
```
followers · following · posts · engagement_rate · avg_likes
avg_comments · avg_views · video_ratio · image_ratio
posting_frequency · creator_score
```

**Output:**
```json
{
  "predicted_price": 12500,
  "price_band": "₹10,625 – ₹14,375",
  "creator_score": 72.4,
  "features_used": { ... }
}
```

### 2 · Risk Prediction Model
> `POST /api/ai/risk/predict`

Classifies collaboration risk using a multi-class classifier with probability calibration.

**Output:**
```json
{
  "risk_category": "Low Risk",
  "risk_label": "Low",
  "risk_score": 0.12,
  "probabilities": { "High Risk": 0.12, "Low Risk": 0.76, "Medium Risk": 0.12 }
}
```

### 3 · Creator Score Model
> `POST /api/ai/score/predict`

Generates a 0–10 composite creator quality score. The score is persisted back to MongoDB after each prediction.

**Output:**
```json
{
  "username": "bhuvan.bam22",
  "creator_score": 7.42
}
```

> All three models can be run **in parallel** via the `predictAll(username)` helper in `api.js`.

---

## 📁 Project Structure

```
collabai/
│
├── frontend/                        # React 19 SPA (Vite)
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.jsx        # Overview + key metrics
│       │   ├── CreatorSearch.jsx    # Search + DB-first lookup
│       │   ├── CreatorProfile.jsx   # Full profile view
│       │   ├── Analytics.jsx        # Charts & trends
│       │   ├── PricePredictor.jsx   # AI pricing UI
│       │   ├── CreateCollaboration.jsx
│       │   └── CollaborationHistory.jsx
│       ├── components/
│       │   ├── Navbar.jsx
│       │   ├── StatsCard.jsx
│       │   ├── ProfileCard.jsx
│       │   └── Charts/
│       │       ├── EngagementChart.jsx
│       │       ├── FollowersChart.jsx
│       │       └── ContentPie.jsx
│       └── services/
│           └── api.js               # Axios client + all API functions
│
└── backend/
    └── app/
        ├── config.py                # Env vars & collection names
        ├── routes/
        │   ├── creator_routes.py    # /api/creator/*
        │   ├── analytics_routes.py  # /api/analytics/*
        │   ├── pricing_routes.py    # /api/ai/price/*
        │   ├── risk_routes.py       # /api/ai/risk/*
        │   ├── creator_score_routes.py  # /api/ai/score/*
        │   ├── collaboration_routes.py  # /api/collaboration/*
        │   ├── brand_routes.py
        │   └── instagram_routes.py
        ├── ml/
        │   ├── ml_service.py        # Unified ML dispatch layer
        │   ├── predict.py           # Price prediction core
        │   ├── prediction.py        # Risk + score prediction
        │   └── models/              # Trained .joblib artifacts
        │       ├── price_model.joblib
        │       ├── scaler.joblib
        │       ├── Risk_Prediction_model.joblib
        │       ├── creator_score_model.joblib
        │       └── ...
        ├── services/
        │   ├── instagram_service.py
        │   ├── scraper_service.py   # SearchAPI integration
        │   └── pricing_services.py
        ├── models/                  # MongoDB document schemas
        │   ├── creator.py
        │   ├── collaboration.py
        │   └── brand.py
        ├── scraper/
        │   ├── profile.py
        │   └── brand.py
        └── utils/
            ├── db.py                # MongoDB connection
            ├── auth.py              # Brand JWT auth
            ├── helpers.py           # Response serializers
            └── validators.py
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js ≥ 18
- Python ≥ 3.11
- MongoDB Atlas URI
- SearchAPI key (for live Instagram scraping)

---

### Backend Setup

```bash
# 1. Navigate to backend
cd backend/app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

Edit `.env`:
```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/
DB_NAME=collabmind
SECRET_KEY=your-secret-key
SEARCHAPI_KEY=your-searchapi-key
PORT=5000
```

```bash
# 5. Run Flask server
python app.py
# → http://127.0.0.1:5000
```

---

### Frontend Setup

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Configure environment
cp .env.example .env
```

Edit `.env`:
```env
VITE_API_URL=http://127.0.0.1:5000
```

```bash
# 4. Start dev server
npm run dev
# → http://localhost:5173
```

---

## 🔌 API Reference

### Creator Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/creator/lookup/:username` | Smart lookup — DB first, scrape on miss |
| `GET` | `/api/creator/username/:username` | Fetch from DB by username |
| `GET` | `/api/creator/profile/:id` | Fetch by MongoDB ObjectId |
| `GET` | `/api/creator/all` | List all stored creators |
| `POST` | `/api/creator/register` | Register a new creator |

### ML / AI Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/ai/price/predict` | `{ username }` → price prediction |
| `POST` | `/api/ai/risk/predict` | `{ username }` → risk classification |
| `POST` | `/api/ai/risk/predict/features` | Raw features → risk (no DB) |
| `POST` | `/api/ai/score/predict` | `{ username }` → creator score |
| `POST` | `/api/ai/score/predict/features` | Raw features → score (no DB) |

### Analytics Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/analytics/dashboard/:id` | Dashboard metrics |
| `GET` | `/api/analytics/engagement/:id` | Engagement time-series |
| `GET` | `/api/analytics/deals/summary/:id` | Deal stats summary |

### Collaboration Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/collaboration/create` | Create a new deal |
| `GET` | `/api/collaboration/list/:creatorId` | List deals for creator |
| `GET` | `/api/collaboration/:id` | Get deal by ID |
| `PUT` | `/api/collaboration/update/:id` | Update deal |
| `DELETE` | `/api/collaboration/:id` | Delete deal |

---

## 🛠️ Tech Stack

**Frontend**
- React 19 · React Router DOM 7 · Vite 7
- Chart.js 4 + react-chartjs-2
- Axios · React Icons · Bootstrap 5

**Backend**
- Flask · PyMongo · python-dotenv
- scikit-learn · NumPy · joblib
- SearchAPI (Instagram scraping)

**Database**
- MongoDB Atlas (collections: `profiles`, `collaborations`, `creator_features`)

---

## 🔮 Future Scope

- [ ] Multi-platform support (YouTube, Twitter/X)
- [ ] Brand dashboard with collaboration ROI tracking
- [ ] Automated outreach templates
- [ ] Real-time webhook for new Instagram posts
- [ ] Model retraining pipeline with new scraped data
- [ ] Export reports as PDF



---

<div align="center">

Built with precision for the creator economy.

</div>

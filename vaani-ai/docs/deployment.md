# Vaani AI — Render Deployment & Production Guide

This guide details the procedure for deploying Vaani AI to [Render](https://render.com) (or any containerized Linux cloud platform like Railway, Fly.io, or Heroku).

---

## 1. Quick Deploy Configuration

### 1.1 Web Service Specifications
- **Environment**: Python
- **Region**: Oregon (US West) or Frankfurt (EU)
- **Branch**: `main`
- **Build Command**:
  ```bash
  pip install --upgrade pip && pip install -r requirements.txt
  ```
- **Start Command**:
  ```bash
  gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
  ```
- **Health Check Path**: `/api/health`

---

## 2. Environment Variables

Configure these variables in your Render Dashboard under **Environment**:

| Variable Name | Required | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `GEMINI_API_KEY` | Recommended | *(none)* | Google Gemini API key for open-ended queries |
| `PYTHON_VERSION` | Yes | `3.11.9` | Recommended Python LTS runtime |
| `FLASK_DEBUG` | No | `0` | Disable debug mode in production |
| `PORT` | Auto | `10000` | Port injected automatically by Render |

---

## 3. Step-by-Step Deployment Instructions

### Step 1: Connect Your GitHub Repository
1. Log into your Render dashboard at [dashboard.render.com](https://dashboard.render.com).
2. Click **New +** $\rightarrow$ **Web Service**.
3. Select **Build and deploy from a Git repository** and link your `vaani-ai` repository.

### Step 2: Configure Service Settings
- **Name**: `vaani-ai` (or your preferred name)
- **Runtime**: `Python 3`
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120`
- **Plan**: `Free` ($0/month, 512 MB RAM, 0.1 CPU)

### Step 3: Add Secrets
1. Navigate to the **Environment** tab.
2. Add `GEMINI_API_KEY` and paste your key.
3. Add `PYTHON_VERSION` with value `3.11.9`.

### Step 4: Deploy & Verify
1. Click **Create Web Service**.
2. Monitor the build logs. Build typically completes in $\approx 60-90\text{ seconds}$.
3. Once deployed, open `https://<your-service>.onrender.com/api/health` to verify that the health check returns HTTP 200 with `status: "healthy"`.

---

## 4. Memory Optimization for Render Free Tier

Render's free tier provides **512 MB RAM**. Vaani AI is engineered specifically to operate well within these constraints:

- **Single Worker with Multithreading**:
  Running Gunicorn with `--workers 1 --threads 4` keeps memory usage around **45–60 MB RAM**, leaving over 400 MB of headroom.
- **Offline Model Pre-Loading**:
  The Word+Char TF-IDF classifier and vectorizer (`models/intent_model.joblib`) consume only **16.6 MB** and are loaded into memory once during startup.
- **Session Memory TTL**:
  Session memory automatically purges conversations inactive for more than 1 hour, preventing RAM accumulation over time.

---

## 5. Troubleshooting & Common Issues

### Issue 1: "Audio format requires FFmpeg"
- **Cause**: User uploaded an `.mp3`, `.m4a`, or `.webm` file on a host without FFmpeg installed.
- **Resolution**: Native PCM WAV, AIFF, and FLAC work without FFmpeg. On custom Docker environments, install `ffmpeg` via `apt-get install -y ffmpeg`.

### Issue 2: "Worker Timeout (120s exceeded)"
- **Cause**: Network lag during external Gemini API calls.
- **Resolution**: Vaani AI enforces a strict 10.0-second timeout on Gemini calls, falling back gracefully to local responses. Gunicorn's `--timeout 120` prevents premature worker kills.

### Issue 3: Free-Tier Spin-Down Delay
- **Behavior**: On Render Free tier, services spin down after 15 minutes of inactivity. The first request may experience a cold start of 30–50 seconds.
- **Resolution**: `/api/health` can be pinged by an external uptime monitor (e.g. UptimeRobot or Cron) to keep the container warm if desired.

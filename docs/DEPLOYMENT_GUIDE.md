# 🚀 Step-by-Step Cloud Deployment Guide (Free Tier)

This guide walks you through deploying the **AI-Powered College Grievance Management System** to the cloud completely free of cost using:
- **Frontend**: [Vercel](https://vercel.com) (or Netlify)
- **Backend**: [Render](https://render.com) (or Railway)
- **Database**: [Neon](https://neon.tech) / [Supabase](https://supabase.com) (or Render PostgreSQL)

---

## 📋 Architecture in Production

```
┌─────────────────────────┐          ┌───────────────────────────┐
│     Vercel Frontend     │  HTTPS   │       Render Backend      │
│ (React + Vite + HTML)   │ ───────> │  (FastAPI + JWT + Python) │
│ https://xxx.vercel.app  │          │ https://xxx.onrender.com  │
└─────────────────────────┘          └─────────────┬─────────────┘
                                                   │
                         ┌─────────────────────────┴─────────────────────────┐
                         ▼                                                   ▼
         ┌───────────────────────────────┐                   ┌───────────────────────────────┐
         │     PostgreSQL Database       │                   │       AI Inference Engine     │
         │  (Neon.tech / Supabase.com)   │                   │ (Local Tunnel / Cloud / Fall) │
         └───────────────────────────────┘                   └───────────────────────────────┘
```

---

## 🗄️ Step 1: Create Free PostgreSQL Database (Neon or Supabase)

1. Go to **[Neon.tech](https://neon.tech)** (Recommended - 100% Free, Instant Setup) or **[Supabase.com](https://supabase.com)**.
2. Sign up / Log in.
3. Click **"New Project"** and name it `ai_grievance_db`.
4. Copy your **PostgreSQL Connection String (URI)**. It will look like:
   ```text
   postgresql://user:password@ep-sample-123456.us-east-2.aws.neon.tech/ai_grievance_db?sslmode=require
   ```
5. Save this URL for Step 2.

---

## ⚡ Step 2: Deploy Backend to Render.com

1. Push your project repository to **GitHub**:
   ```bash
   git add .
   git commit -m "Prepare cloud deployment configs"
   git push origin main
   ```
2. Go to **[Render.com](https://render.com)** and create a free account.
3. In the Render Dashboard, click **"New +"** → **"Web Service"**.
4. Connect your GitHub repository.
5. Configure the Web Service settings:
   - **Name**: `ai-grievance-backend`
   - **Region**: Closest to you (e.g. *Oregon* or *Frankfurt*)
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`

6. Under **"Environment Variables"**, add:
   | Key | Value |
   |---|---|
   | `DATABASE_URL` | `postgresql://user:password@ep-sample-123456.neon.tech/ai_grievance_db?sslmode=require` |
   | `JWT_SECRET_KEY` | *(Click "Generate" or type a random 32-char string)* |
   | `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |
   | `OLLAMA_URL` | `http://localhost:11434/api/generate` *(or your tunnel URL)* |
   | `PYTHON_VERSION` | `3.11.8` |

7. Click **"Deploy Web Service"**.
8. Once finished, Render will assign your backend a live URL, e.g.:
   ```text
   https://ai-grievance-backend.onrender.com
   ```
   Test it in your browser: `https://ai-grievance-backend.onrender.com/docs`

---

## 🎨 Step 3: Deploy Frontend to Vercel

1. Go to **[Vercel.com](https://vercel.com)** and log in with your GitHub account.
2. Click **"Add New..."** → **"Project"**.
3. Select your GitHub repository.
4. Configure the Project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click `Edit` and choose `frontend`.
5. Under **"Environment Variables"**, add:
   | Key | Value |
   |---|---|
   | `VITE_API_URL` | `https://ai-grievance-backend.onrender.com` *(Your Render backend URL from Step 2, no trailing slash)* |

6. Click **"Deploy"**.
7. In ~30 seconds, Vercel will give you a live production URL, e.g.:
   ```text
   https://ai-grievance-frontend.vercel.app
   ```

---

## 🤖 Step 4: AI Model Handling in Cloud

Because free cloud servers (512MB RAM) cannot run a 3.2B parameter LLM locally:

### Option A: Built-in Smart Fallback Engine (Zero configuration required)
- The backend contains a built-in deterministic heuristic classifier. If Ollama is not on the cloud instance, it categorizes grievances into the 6 categories, assigns priority, and generates summaries without any paid API keys or additional configuration.

### Option B: Connect to your Local Ollama via Cloudflare Tunnel (Free & Easy)
To let your cloud backend query your actual local computer's Ollama Llama 3.2 3B instance:
1. On your computer with Ollama running, download [Cloudflare Tunnel (cloudflared)](https://github.com/cloudflare/cloudflared/releases).
2. Run:
   ```bash
   cloudflared tunnel --url http://localhost:11434
   ```
3. Cloudflare gives you a secure HTTPS URL, e.g. `https://random-words.trycloudflare.com`.
4. Set `OLLAMA_URL` in your Render Environment Variables to:
   ```text
   https://random-words.trycloudflare.com/api/generate
   ```

---

## 🔑 Step 5: Verify & Log In to Your Live App

1. Open your Vercel URL in your browser: `https://your-app.vercel.app`.
2. The database will auto-seed the default demo accounts on first launch:
   - **Student Demo**: `student@college.edu` / `student123`
   - **Admin Demo**: `admin@college.edu` / `admin123`
3. Click the instant login buttons to test grievance submissions and administrative status updates live on the internet!

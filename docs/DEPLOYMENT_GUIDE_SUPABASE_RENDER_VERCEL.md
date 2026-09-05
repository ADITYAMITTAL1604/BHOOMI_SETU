# BhoomiSetu Cloud Deployment Guide
## Stack: Supabase (PostgreSQL + PostGIS) + Render (Backend) + Vercel (Frontend)

This guide walks you through deploying **BhoomiSetu** to production in under 15 minutes using 100% free tiers.

---

### Prerequisites & Architecture

```
[ Vercel Edge CDN ]          [ Render Web Service ]          [ Supabase Cloud ]
React 18 + Vite (Frontend) -> FastAPI + PostGIS (Backend) -> PostgreSQL 15 + PostGIS
(https://your-app.vercel.app) (https://your-api.onrender.com) (db.xxx.supabase.co:5432)
```

---

## Part 1: Setup PostgreSQL + PostGIS on Supabase (2 minutes)

1. Go to [supabase.com](https://supabase.com) and sign in.
2. Click **New Project**:
   - **Name**: `bhoomisetu-db`
   - **Database Password**: Set a strong password (save this!).
   - **Region**: Choose the region closest to your users (e.g. `South Asia (Mumbai)`).
   - Click **Create new project**.
3. **Enable PostGIS Extension**:
   - In the left sidebar, navigate to **Database** → **Extensions**.
   - Search for `postgis`.
   - Toggle the switch to **ON** (Enabled).
4. **Copy Database Connection String**:
   - In the left sidebar, click **Project Settings** (gear icon) → **Database**.
   - Scroll to **Connection string** and select the **URI** tab.
   - Choose **Session mode** (or **Direct connection** on port 5432):
     ```text
     postgresql://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres
     ```
   - Replace `[YOUR-PASSWORD]` with your actual database password.

---

## Part 2: Deploy Backend on Render (5 minutes)

1. Go to [render.com](https://render.com) and sign in with GitHub.
2. Click **New +** → **Web Service**.
3. Connect your GitHub repository: `Singh4Ashmeet/BHOOMI_SETU`.
4. Configure service settings:
   - **Name**: `bhoomisetu-api`
   - **Region**: Same or nearest region to your Supabase project (e.g. `Singapore` or `Frankfurt`).
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: `Free`
5. Click **Advanced** → **Add Environment Variable**:

| Variable Name | Value | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://postgres.[REF]:[PASSWORD]@...` *(from Part 1)* | Connects backend to Supabase PostGIS |
| `ENVIRONMENT` | `production` | Enables production security checks |
| `JWT_SECRET` | *(Generate a random 32-char key below)* | Cryptographic JWT signing key |
| `DATA_SOURCE` | `synthetic` | Ingests 15 projects & 808 parcels on first launch |
| `CORS_ORIGINS` | `*` | Allows cross-origin API requests from Vercel |

> **Generate JWT_SECRET**:
> ```bash
> python -c "import secrets; print(secrets.token_urlsafe(32))"
> ```

6. Click **Create Web Service**.
7. Render will build the image, start Uvicorn, connect to Supabase, run PostGIS extensions, create all tables, and auto-seed the canonical dataset.
8. Once the build displays `Application startup complete`, copy your public Render URL:
   `https://bhoomisetu-api.onrender.com`

---

## Part 3: Deploy Frontend on Vercel (3 minutes)

1. Go to [vercel.com](https://vercel.com) and sign in with GitHub.
2. Click **Add New...** → **Project**.
3. Import the `Singh4Ashmeet/BHOOMI_SETU` repository.
4. Configure project settings:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click `Edit` and select `frontend`.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Expand **Environment Variables**:

| Key | Value |
| :--- | :--- |
| `VITE_API_BASE_URL` | `https://bhoomisetu-api.onrender.com/api/v1` *(your Render URL + `/api/v1`)* |

6. Click **Deploy**.
7. Vercel will compile TypeScript, bundle assets, and deploy to their global CDN.

---

## Part 4: Production Verification

1. Open your live Vercel URL (e.g. `https://bhoomi-setu.vercel.app`).
2. The login page will display the **Quick Demo Accounts** card:
   - Click **Admin** (`admin` / `password123`) to view the National Command Dashboard.
   - Click **State User** (`state_user` / `password123`) to view State-level monitoring.
   - Click **Field Officer** (`field_officer` / `password123`) to view Ground Survey monitoring.
3. Test GIS parcels map, statutory stepper, bottleneck alerts, and ML risk scores. Everything will be backed by live PostGIS on Supabase!

# Civitas Production Deployment Guide

This guide walks you through deploying the **Civitas Frontend** on **Vercel** and the **Civitas Backend API** on **Render**.

---

## 1. Deploying Backend API to Render

### Option A: Via Render Blueprints (Recommended)
1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository: `Dhruvg334/Civitas`.
4. Render will automatically detect `render.yaml` and configure the `civitas-api` web service.
5. In the Environment Variables screen, fill in your secrets:
   - `DATABASE_URL`: `postgresql://postgres.mxuoyknmotadvqemrnbo:civitas%406289584219@aws-0-ap-south-1.pooler.supabase.com:5432/postgres`
   - `SUPABASE_URL`: `https://mxuoyknmotadvqemrnbo.supabase.co`
   - `SUPABASE_ANON_KEY`: `<your-supabase-anon-key>`
   - `SUPABASE_SERVICE_ROLE_KEY`: `<your-supabase-service-role-key>`
   - `GROQ_API_KEY`: `<your-groq-api-key>`
   - `CORS_ORIGINS`: `*` (or your Vercel domain URL)
6. Click **Apply**. Render will build the Docker container and expose your public API at:
   `https://civitas-api.onrender.com` (or similar).

### Option B: Manual Web Service
- **Runtime**: Docker
- **Docker Context**: `.` (root)
- **Dockerfile Path**: `apps/api/Dockerfile`
- **Health Check Path**: `/ready`

---

## 2. Deploying Frontend Web App to Vercel

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import the `Dhruvg334/Civitas` GitHub repository.
4. In the Project Configuration:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `./` (or `apps/web`)
   - **Build Command**: `npm --workspace apps/web run build`
   - **Output Directory**: `apps/web/.next`
   - **Install Command**: `npm install`
5. In **Environment Variables**, add:
   - `NEXT_PUBLIC_API_BASE_URL`: `https://civitas-api.onrender.com/api/v1` (replace with your actual Render API URL)
   - `NEXT_PUBLIC_SUPABASE_URL`: `https://mxuoyknmotadvqemrnbo.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: `<your-supabase-anon-key>`
6. Click **Deploy**. Vercel will build the production bundle and assign your live domain (e.g., `https://civitas.vercel.app`).

---

## 3. Post-Deployment Verification

1. **Verify Backend Health**:
   ```bash
   curl -i https://civitas-api.onrender.com/ready
   # Expected: {"service":"Civitas API","status":"ready"}
   ```
2. **Verify Frontend Incidents**:
   Navigate to `https://<your-vercel-domain>/workspace` to view live synced PostGIS incidents and Leaflet GIS maps.

# Civitas Production Deployment Guide

This guide walks you through deploying the **Civitas Frontend** on **Vercel** (`https://civitas-web.vercel.app`) and the **Civitas Backend API** on **Render**.

---

## 1. Database & Migrations Setup (Supabase / PostgreSQL + PostGIS)

Before starting the API service, apply the database migrations in sequential order against your PostgreSQL database:

```bash
psql "$DATABASE_URL" -f database/migrations/0001_spatial_core.sql
psql "$DATABASE_URL" -f database/migrations/0002_incident_description.sql
psql "$DATABASE_URL" -f database/migrations/0003_incident_operations.sql
psql "$DATABASE_URL" -f database/migrations/0004_workflow_core.sql
psql "$DATABASE_URL" -f database/migrations/0005_seed_policies.sql
psql "$DATABASE_URL" -f database/migrations/0006_workflow_runs.sql
```

> **Note**: LangGraph's low-level checkpoint tables (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`) are automatically initialized on startup via `create_postgres_checkpointer().setup()` using `CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL`.

---

## 2. Deploying Backend API to Render

### Option A: Via Render Blueprint (`render.yaml`) (Recommended)
1. Log into your [Render Dashboard](https://dashboard.render.com).
2. Click **New +** → **Blueprint**.
3. Connect your GitHub repository: `Dhruvg334/Civitas`.
4. Render will automatically detect `render.yaml` and configure the `civitas-api` web service.
5. In the Environment Variables screen, provide your secrets:
   - `DATABASE_URL`: `postgresql://postgres:<password>@<db-host>:5432/postgres`
   - `CIVITAS_WORKFLOW_CHECKPOINT_DATABASE_URL`: `postgresql://postgres:<password>@<db-host>:5432/postgres`
   - `CIVITAS_POSTGIS_DSN`: `postgresql://postgres:<password>@<db-host>:5432/postgres`
   - `SUPABASE_URL`: `https://<project-ref>.supabase.co`
   - `SUPABASE_ANON_KEY`: `<your-supabase-anon-key>`
   - `SUPABASE_SERVICE_ROLE_KEY`: `<your-supabase-service-role-key>`
   - `SUPABASE_JWT_SECRET`: `<your-supabase-jwt-secret>`
   - `GROQ_API_KEY`: `<your-groq-api-key>`
   - `CORS_ORIGINS`: `https://civitas-web.vercel.app`
6. Click **Apply**. Render will build the Docker container using `apps/api/Dockerfile` and expose your public API at:
   `https://civitas-api.onrender.com` (or your chosen service subdomain).

### Option B: Manual Web Service
- **Runtime**: Docker
- **Docker Context**: `.` (root)
- **Dockerfile Path**: `apps/api/Dockerfile`
- **Health Check Path**: `/ready`
- **Port**: Bound dynamically via `${PORT:-8000}`

---

## 3. Deploying Frontend Web App to Vercel

1. Log into your [Vercel Dashboard](https://vercel.com).
2. Click **Add New...** → **Project**.
3. Import the `Dhruvg334/Civitas` GitHub repository.
4. In the Project Configuration:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: `./`
   - **Build Command**: `node scripts/build-web.mjs`
   - **Output Directory**: `apps/web/.next`
   - **Install Command**: `npm install`
5. In **Environment Variables**, add:
   - `NEXT_PUBLIC_API_BASE_URL`: `https://civitas-api.onrender.com/api/v1` (replace with your Render service URL)
   - `NEXT_PUBLIC_SUPABASE_URL`: `https://<project-ref>.supabase.co`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`: `<your-supabase-anon-key>`
   - `NEXT_PUBLIC_CIVITAS_DEMO_MODE`: `false` (set `true` only for offline showcase mode)
6. Click **Deploy**. Vercel will deploy the production web app at `https://civitas-web.vercel.app`.

---

## 4. Supabase Authentication Configuration

1. In Supabase Dashboard → **Authentication** → **URL Configuration**:
   - **Site URL**: `https://civitas-web.vercel.app`
   - **Redirect URLs**:
     - `https://civitas-web.vercel.app/**`
     - `http://localhost:3000/**` (for local development)
2. In Supabase Dashboard → **Authentication** → **Email Templates**:
   - Ensure Reset Password and Confirmation links route to `https://civitas-web.vercel.app/reset-password`.

---

## 5. Post-Deployment Verification

1. **Verify Backend Health**:
   ```bash
   curl -i https://civitas-api.onrender.com/ready
   # Expected: {"service":"civitas-api","status":"ready","database":"ok","environment":"production"}
   ```
2. **Verify Frontend**:
   Navigate to `https://civitas-web.vercel.app/workspace` to confirm live report sync, incident triage, and PostGIS geofenced maps.

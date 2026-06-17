#!/usr/bin/env bash
# deploy.sh — build, push, and deploy the BigQuery SQL Agent to Cloud Run.
# Run once to deploy; re-run to update.
#
# Prerequisites (one-time):
#   gcloud auth login
#   gcloud config set project msbai-dwd-sk7374
#
# The Cloud Run service runs as bq-sql-agent@... which needs:
#   roles/bigquery.jobUser        — already granted (runs BQ jobs)
#   roles/aiplatform.user         — needed for Vertex AI (Gemini); grant with:
#     gcloud projects add-iam-policy-binding msbai-dwd-sk7374 \
#       --member="serviceAccount:bq-sql-agent@msbai-dwd-sk7374.iam.gserviceaccount.com" \
#       --role="roles/aiplatform.user"
#
# Secrets: LANGCHAIN_API_KEY must exist in Secret Manager before first deploy:
#   echo -n "lsv2_..." | gcloud secrets create langchain-api-key --data-file=-
#   gcloud secrets add-iam-policy-binding langchain-api-key \
#     --member="serviceAccount:bq-sql-agent@msbai-dwd-sk7374.iam.gserviceaccount.com" \
#     --role="roles/secretmanager.secretAccessor"

set -euo pipefail

PROJECT_ID="msbai-dwd-sk7374"
REGION="us-central1"
SERVICE_NAME="bq-sql-agent"
REPO="bigquery-sql-agent"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/api"
SERVICE_ACCOUNT="bq-sql-agent@${PROJECT_ID}.iam.gserviceaccount.com"

# ── 1. Enable required APIs (idempotent) ────────────────────────────────────
echo "→ Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  aiplatform.googleapis.com \
  --project="${PROJECT_ID}" --quiet

# ── 2. Create Artifact Registry repo if it doesn't exist ────────────────────
if ! gcloud artifacts repositories describe "${REPO}" \
     --location="${REGION}" --project="${PROJECT_ID}" &>/dev/null; then
  echo "→ Creating Artifact Registry repository..."
  gcloud artifacts repositories create "${REPO}" \
    --repository-format=docker \
    --location="${REGION}" \
    --project="${PROJECT_ID}"
fi

# ── 3. Authenticate Docker to Artifact Registry ─────────────────────────────
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# ── 4. Build and push ────────────────────────────────────────────────────────
echo "→ Building and pushing ${IMAGE}..."
docker build --platform linux/amd64 -t "${IMAGE}" .
docker push "${IMAGE}"

# ── 5. Deploy to Cloud Run ───────────────────────────────────────────────────
echo "→ Deploying to Cloud Run..."
gcloud run deploy "${SERVICE_NAME}" \
  --image="${IMAGE}" \
  --platform=managed \
  --region="${REGION}" \
  --project="${PROJECT_ID}" \
  --service-account="${SERVICE_ACCOUNT}" \
  --allow-unauthenticated \
  --port=8080 \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=120 \
  --set-env-vars="BQ_BILLING_PROJECT=${PROJECT_ID},BQ_PROJECT_ID=bigquery-public-data,BQ_DATASET=new_york_citibike,LANGCHAIN_TRACING_V2=true,LANGCHAIN_PROJECT=bigquery-sql-agent,CORS_ORIGINS=https://sanchitk.dev" \
  --set-secrets="LANGCHAIN_API_KEY=langchain-api-key:latest" \
  --quiet

# ── 6. Print service URL ─────────────────────────────────────────────────────
URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --platform=managed --region="${REGION}" --project="${PROJECT_ID}" \
  --format="value(status.url)")
echo ""
echo "✓ Deployed: ${URL}"
echo "  Health:   ${URL}/health"
echo "  Widget:   set data-api-url=\"${URL}\" in the frontend <div>"

# Render deployment

Render is recommended for this project because the backend is a long-running
FastAPI service with WebSocket support. Vercel is a poor fit for the backend
because its serverless function bundle limits do not match the ML dependencies.

## Deploy with the Blueprint

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint** and select the repository.
3. Render will read `render.yaml` and create the free API and frontend services.
4. After the first deploy, copy the actual frontend URL from Render.
5. In the `sentinelml-api` service, set `CORS_ALLOWED_ORIGINS` to a JSON array containing that exact URL, for example:

   ```text
   ["https://sentinelml-web-xxxx.onrender.com"]
   ```

6. Update `VITE_API_BASE_URL` and `VITE_WS_URL` in the frontend service if Render assigned a different API hostname, then redeploy the frontend.

The API health check is available at `/health`, and the API documentation is at
`/docs` on the API service.

## Free-tier limitation

Render's free service filesystem is ephemeral and the service can sleep. This
deployment is suitable for a portfolio demo, but the SQLite database, uploaded
datasets, MLflow files, and trained model artifacts may be lost after a restart.
For durable data, use a managed PostgreSQL database and object storage, then set
`DATABASE_URL`, `DATA_DIR`, `MODEL_STORE_DIR`, and MLflow storage accordingly.
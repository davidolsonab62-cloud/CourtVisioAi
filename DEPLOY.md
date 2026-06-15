Deployment guide
================

This repository is configured to deploy the frontend to Vercel and trigger a backend deploy on Render using GitHub Actions.

Required repository secrets (Settings → Secrets → Actions):

- `VERCEL_TOKEN` — Vercel personal token
- `VERCEL_ORG_ID` — Vercel organization id
- `VERCEL_PROJECT_ID` — Vercel project id for the frontend
- `RENDER_API_KEY` — Render API key (service-level)
- `RENDER_SERVICE_ID` — Render service ID for your backend

How it works
------------

- On push to `main`, GitHub Actions will build the frontend (`frontend/`) and deploy it to Vercel using the `amondnet/vercel-action` action.
- After frontend build, the workflow will POST to the Render API to create a new deploy for the configured backend service.

Setting secrets
---------------

1. Vercel: create a personal token in your Vercel account and set `VERCEL_TOKEN`. Create a project in Vercel and note the `orgId` and `projectId` (available in the project settings or API).
2. Render: create an API key in the Render dashboard and note your backend service's `serviceId` (it appears in the service URL or service settings).

Manual deploy
-------------

- To manually trigger a backend deploy without waiting for a Git push, use the following curl (replace placeholders):

```bash
curl -X POST "https://api.render.com/v1/services/<SERVICE_ID>/deploys" \
  -H "Authorization: Bearer <RENDER_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"clearCache":true}'
```

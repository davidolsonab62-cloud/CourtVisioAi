"""CourtVision AI – FastAPI entry."""
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from db import init_db, ensure_indexes, close_db
from routes_auth import router as auth_router
from routes_core import router as core_router
from routes_admin import router as admin_router
from routes_payments import router as payments_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await ensure_indexes()
    try:
        from seed_runtime import run_seed
        await run_seed()
    except Exception as e:
        logger.exception(f"Seed failed: {e}")
    yield
    close_db()


app = FastAPI(title="CourtVision AI", lifespan=lifespan)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "courtvision-ai"}


app.include_router(auth_router)
app.include_router(core_router)
app.include_router(admin_router)
app.include_router(payments_router)


cors_origins_env = os.environ.get("CORS_ORIGINS", "*")
frontend_url = os.environ.get("FRONTEND_URL", "")
raw_list = [frontend_url] if frontend_url and frontend_url != "*" else (cors_origins_env.split(",") if cors_origins_env != "*" else ["*"])
# Normalize origins: strip whitespace and remove empty entries
allow_origins = [o.strip() for o in raw_list if o and o.strip()]
# When using credentialed cookies, "*" is invalid; fall back to FRONTEND_URL if set
if "*" in allow_origins and frontend_url:
    allow_origins = [frontend_url]

# Allow localhost origins via regex fallback (handles different dev ports)
allow_origin_regex = None
try:
    if any(o.startswith("http://localhost") or o.startswith("http://127.0.0.1") for o in allow_origins if o):
        allow_origin_regex = r"^https?://(localhost|127\\.0\\.0\\.1)(:[0-9]+)?$"
except Exception:
    allow_origin_regex = None

logger.info(f"CORS config: allow_origins={allow_origins} allow_origin_regex={allow_origin_regex}")

from fastapi import Request, Response

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)



@app.get("/api/debug/headers")
async def debug_headers(request: Request):
    return {k: v for k, v in request.headers.items()}

"""Admin endpoints."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from db import get_db
from auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
async def admin_dashboard(_=Depends(require_admin)):
    db = get_db()
    total_users = await db.users.count_documents({})
    premium_users = await db.users.count_documents({"role": "premium"})
    admin_users = await db.users.count_documents({"role": "admin"})
    total_games = await db.games.count_documents({})
    total_predictions = await db.predictions.count_documents({})
    finished_preds = await db.predictions.count_documents({"was_correct": {"$ne": None}})
    wins = await db.predictions.count_documents({"was_correct": True})
    accuracy = round(wins / finished_preds * 100, 1) if finished_preds else 0
    revenue = await db.payment_transactions.aggregate([
        {"$match": {"payment_status": "paid"}},
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}},
    ]).to_list(1)
    revenue_total = revenue[0]["total"] if revenue else 0
    return {
        "total_users": total_users,
        "premium_users": premium_users,
        "admin_users": admin_users,
        "total_games": total_games,
        "total_predictions": total_predictions,
        "accuracy": accuracy,
        "revenue_total": round(revenue_total, 2),
    }


@router.get("/users")
async def list_users(_=Depends(require_admin)):
    db = get_db()
    raw = await db.users.find({}, {"password_hash": 0}).to_list(1000)
    out = []
    for u in raw:
        out.append({
            "id": str(u["_id"]),
            "email": u.get("email"),
            "name": u.get("name"),
            "role": u.get("role"),
            "premium_until": u.get("premium_until"),
            "favorites": u.get("favorites", []),
            "created_at": u.get("created_at"),
        })
    return out


class RoleUpdate(BaseModel):
    role: str  # "user" | "premium" | "admin" | "suspended"


@router.patch("/users/{user_id}/role")
async def update_role(user_id: str, payload: RoleUpdate, _=Depends(require_admin)):
    if payload.role not in {"user", "premium", "admin", "suspended"}:
        raise HTTPException(400, "Invalid role")
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user id")
    update = {"role": payload.role}
    if payload.role == "premium":
        update["premium_until"] = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    res = await db.users.update_one({"_id": oid}, {"$set": update})
    if res.matched_count == 0:
        raise HTTPException(404, "User not found")
    return {"ok": True}


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, _=Depends(require_admin)):
    db = get_db()
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(400, "Invalid user id")
    await db.users.delete_one({"_id": oid})
    return {"ok": True}


@router.get("/predictions")
async def admin_predictions(_=Depends(require_admin)):
    db = get_db()
    preds = await db.predictions.find({}, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
    return preds


@router.get("/revenue")
async def admin_revenue(_=Depends(require_admin)):
    db = get_db()
    txns = await db.payment_transactions.find({}, {"_id": 0}).sort("created_at", -1).limit(200).to_list(200)
    return txns


@router.get("/api-keys")
async def admin_api_keys(_=Depends(require_admin)):
    import os
    return {
        "api_sports": {"configured": bool(os.environ.get("API_SPORTS_KEY")), "host": os.environ.get("API_SPORTS_HOST")},
        "stripe": {"configured": bool(os.environ.get("STRIPE_API_KEY"))},
    }


@router.get("/logs")
async def admin_logs(_=Depends(require_admin)):
    db = get_db()
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("ts", -1).limit(100).to_list(100)
    return logs


@router.get("/ml/meta")
async def ml_meta(_=Depends(require_admin)):
    import ml_engine
    meta = ml_engine.load_meta()
    return {
        "trained": ml_engine.is_trained(),
        "meta": meta,
    }


@router.post("/ml/retrain")
async def ml_retrain(_=Depends(require_admin)):
    from seed_runtime import train_ml_models, regenerate_predictions
    meta = await train_ml_models(force=True)
    await regenerate_predictions()
    return {"ok": True, "meta": meta}


@router.get("/api-sports/test")
async def api_sports_test(_=Depends(require_admin)):
    """Hit api-sports.io with the configured key. Returns a small probe payload."""
    import os
    import httpx
    key = os.environ.get("API_SPORTS_KEY", "")
    host = os.environ.get("API_SPORTS_HOST", "v1.basketball.api-sports.io")
    if not key:
        raise HTTPException(400, "API_SPORTS_KEY not configured. Add it to backend/.env and restart.")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                f"https://{host}/status",
                headers={"x-rapidapi-key": key, "x-rapidapi-host": host},
            )
            data = r.json()
            return {"ok": r.status_code == 200, "status_code": r.status_code, "host": host, "response": data}
    except Exception as e:
        raise HTTPException(502, f"api-sports request failed: {e}")

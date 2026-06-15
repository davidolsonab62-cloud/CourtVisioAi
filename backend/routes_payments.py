"""Stripe subscription endpoints."""
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from db import get_db
from auth import get_current_user, get_optional_user

try:
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout, CheckoutSessionRequest,
    )
    payments_enabled = True
except ImportError:
    try:
        import stripe

        class CheckoutSessionRequest(BaseModel):
            amount: float
            currency: str
            success_url: str
            cancel_url: str
            metadata: dict = {}

        class StripeCheckout:
            def __init__(self, api_key: str, webhook_url: str):
                stripe.api_key = api_key
                self.webhook_url = webhook_url

            async def create_checkout_session(self, req: CheckoutSessionRequest):
                session = stripe.checkout.Session.create(
                    payment_method_types=["card"],
                    line_items=[
                        {
                            "price_data": {
                                "currency": req.currency,
                                "product_data": {"name": "CourtVision AI Premium"},
                                "unit_amount": int(round(req.amount * 100)),
                            },
                            "quantity": 1,
                        }
                    ],
                    mode="payment",
                    success_url=req.success_url,
                    cancel_url=req.cancel_url,
                    metadata=req.metadata,
                )
                return type("CheckoutSession", (), {"session_id": session.id, "url": session.url})

            async def get_checkout_status(self, session_id: str):
                session = stripe.checkout.Session.retrieve(session_id, expand=["payment_intent"])
                return type(
                    "CheckoutStatus",
                    (),
                    {
                        "payment_status": session.payment_status,
                        "status": session.status,
                        "amount_total": session.amount_total,
                        "currency": session.currency,
                    },
                )

        payments_enabled = True
    except ImportError:
        StripeCheckout = None
        CheckoutSessionRequest = None
        payments_enabled = False

router = APIRouter(prefix="/api", tags=["payments"])

# Fixed packages — never trust frontend prices
PACKAGES = {
    "weekly":    {"amount": 9.99,  "days": 7,   "label": "Weekly Pass"},
    "monthly":   {"amount": 29.99, "days": 30,  "label": "Monthly Pro"},
    "quarterly": {"amount": 79.99, "days": 90,  "label": "Quarterly Edge"},
    "yearly":    {"amount": 249.99, "days": 365, "label": "Season Vault"},
}


class CheckoutIn(BaseModel):
    package_id: str
    origin_url: str


@router.get("/packages")
async def list_packages():
    return [{"id": k, **v} for k, v in PACKAGES.items()]


def _ensure_payments_enabled():
    if not payments_enabled:
        raise HTTPException(status_code=503, detail="Payments are not available in this environment")


@router.post("/checkout/session")
async def create_checkout(payload: CheckoutIn, request: Request, user=Depends(get_current_user)):
    _ensure_payments_enabled()
    pkg = PACKAGES.get(payload.package_id)
    if not pkg:
        raise HTTPException(400, "Invalid package")

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe = StripeCheckout(api_key=os.environ["STRIPE_API_KEY"], webhook_url=webhook_url)

    success_url = f"{payload.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{payload.origin_url}/pricing"
    metadata = {
        "user_id": user["id"],
        "user_email": user["email"],
        "package_id": payload.package_id,
        "days": str(pkg["days"]),
    }
    req = CheckoutSessionRequest(
        amount=float(pkg["amount"]),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata=metadata,
    )
    session = await stripe.create_checkout_session(req)
    db = get_db()
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": user["id"],
        "user_email": user["email"],
        "package_id": payload.package_id,
        "amount": pkg["amount"],
        "currency": "usd",
        "payment_status": "pending",
        "status": "initiated",
        "metadata": metadata,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    return {"url": session.url, "session_id": session.session_id}


async def _grant_premium(user_email: str, days: int):
    db = get_db()
    now = datetime.now(timezone.utc)
    user = await db.users.find_one({"email": user_email})
    base = now
    if user and user.get("premium_until"):
        try:
            current = datetime.fromisoformat(user["premium_until"])
            if current.tzinfo is None:
                current = current.replace(tzinfo=timezone.utc)
            if current > now:
                base = current
        except Exception:
            pass
    new_until = (base + timedelta(days=days)).isoformat()
    await db.users.update_one(
        {"email": user_email},
        {"$set": {"role": "premium", "premium_until": new_until}},
    )


@router.get("/checkout/status/{session_id}")
async def checkout_status(session_id: str, request: Request, user=Depends(get_current_user)):
    _ensure_payments_enabled()
    db = get_db()
    txn = await db.payment_transactions.find_one({"session_id": session_id})
    if not txn:
        raise HTTPException(404, "Transaction not found")
    if txn.get("payment_status") == "paid":
        return {"payment_status": "paid", "status": "complete", "already_processed": True}

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe = StripeCheckout(api_key=os.environ["STRIPE_API_KEY"], webhook_url=webhook_url)
    status = await stripe.get_checkout_status(session_id)

    update = {
        "payment_status": status.payment_status,
        "status": status.status,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payment_transactions.update_one({"session_id": session_id}, {"$set": update})

    if status.payment_status == "paid" and txn.get("payment_status") != "paid":
        days = int(txn.get("metadata", {}).get("days", 30))
        await _grant_premium(txn["user_email"], days)

    return {"payment_status": status.payment_status, "status": status.status, "amount_total": status.amount_total, "currency": status.currency}


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    _ensure_payments_enabled()
    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe = StripeCheckout(api_key=os.environ["STRIPE_API_KEY"], webhook_url=webhook_url)
    try:
        evt = await stripe.handle_webhook(body, sig)
    except Exception as e:
        raise HTTPException(400, f"Invalid webhook: {e}")
    db = get_db()
    if evt.payment_status == "paid" and evt.session_id:
        txn = await db.payment_transactions.find_one({"session_id": evt.session_id})
        if txn and txn.get("payment_status") != "paid":
            await db.payment_transactions.update_one(
                {"session_id": evt.session_id},
                {"$set": {"payment_status": "paid", "status": "complete"}},
            )
            days = int(txn.get("metadata", {}).get("days", 30))
            await _grant_premium(txn["user_email"], days)
    return {"ok": True}

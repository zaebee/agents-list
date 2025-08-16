#!/usr/bin/env python3
"""
Billing API for AI-CRM System

This module provides REST API endpoints for billing, subscription management,
and usage tracking. Integrates with the pricing models and supports Stripe
for payment processing.
"""

from datetime import datetime, timedelta
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
import stripe

from pricing_models import (
    PricingManager,
    SubscriptionTier,
    UsageMetrics,
    get_pricing_for_api,
    pricing_manager,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# FastAPI router
router = APIRouter(prefix="/api/billing", tags=["billing"])
security = HTTPBearer()


# Pydantic models for API requests/responses
class SubscriptionRequest(BaseModel):
    tier: str = Field(..., description="Subscription tier (free, pro, enterprise)")
    billing_cycle: str = Field(
        default="monthly", description="Billing cycle (monthly, annual)"
    )
    seats: int = Field(default=1, ge=1, description="Number of user seats")


class SubscriptionResponse(BaseModel):
    subscription_id: str
    tier: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    next_billing_date: datetime
    amount: float
    currency: str


class UsageResponse(BaseModel):
    user_id: str
    subscription_tier: str
    current_usage: dict[str, Any]
    limits: dict[str, Any]
    billing_summary: dict[str, Any]
    recommendations: list[dict[str, Any]]


class PaymentMethodRequest(BaseModel):
    payment_method_id: str
    set_as_default: bool = True


# Mock user database (replace with real database in production)
users_db = {}
subscriptions_db = {}


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Extract user from JWT token (simplified version)."""
    # In production, decode JWT and validate
    # For now, return mock user based on token
    token = credentials.credentials
    if token == "demo_token":
        return {"user_id": "demo_user", "email": "demo@example.com"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication token"
    )


@router.get("/pricing", summary="Get pricing plans")
async def get_pricing():
    """
    Get all available pricing plans with features and pricing information.
    """
    try:
        return get_pricing_for_api()
    except Exception as e:
        logger.error(f"Error getting pricing plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pricing information",
        )


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(current_user: dict = Depends(get_current_user)):
    """
    Get current subscription details for the authenticated user.
    """
    user_id = current_user["user_id"]

    # Get subscription from database (mock implementation)
    subscription = subscriptions_db.get(user_id)

    if not subscription:
        # Return default free subscription
        return SubscriptionResponse(
            subscription_id=f"free_{user_id}",
            tier="free",
            status="active",
            current_period_start=datetime.now(),
            current_period_end=datetime.now() + timedelta(days=30),
            next_billing_date=datetime.now() + timedelta(days=30),
            amount=0.0,
            currency="USD",
        )

    return SubscriptionResponse(**subscription)


@router.post("/subscription", response_model=SubscriptionResponse)
async def create_subscription(
    request: SubscriptionRequest, current_user: dict = Depends(get_current_user)
):
    """
    Create or update subscription for the authenticated user.
    """
    user_id = current_user["user_id"]

    try:
        # Validate subscription tier
        try:
            tier = SubscriptionTier(request.tier.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid subscription tier: {request.tier}",
            )

        # Get pricing information
        plan = pricing_manager.get_pricing_plan(tier)

        if request.billing_cycle == "annual":
            amount = plan.price_per_year * request.seats
        else:
            amount = plan.price_per_month * request.seats

        # For free tier, no payment processing needed
        if tier == SubscriptionTier.FREE:
            subscription_data = {
                "subscription_id": f"free_{user_id}",
                "tier": request.tier.lower(),
                "status": "active",
                "current_period_start": datetime.now(),
                "current_period_end": datetime.now() + timedelta(days=30),
                "next_billing_date": datetime.now() + timedelta(days=30),
                "amount": 0.0,
                "currency": "USD",
            }
        else:
            # Create Stripe subscription for paid tiers
            if not stripe.api_key:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Payment processing not configured",
                )

            # Create Stripe customer if doesn't exist
            customer = stripe.Customer.create(
                email=current_user["email"], metadata={"user_id": user_id}
            )

            # Create price object in Stripe
            price = stripe.Price.create(
                unit_amount=int(amount * 100),  # Stripe uses cents
                currency="usd",
                recurring={
                    "interval": "month"
                    if request.billing_cycle == "monthly"
                    else "year"
                },
                product_data={
                    "name": f"AI-CRM {plan.name}",
                    "description": f"{plan.name} subscription",
                },
            )

            # Create subscription
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": price.id, "quantity": request.seats}],
                payment_behavior="default_incomplete",
                expand=["latest_invoice.payment_intent"],
            )

            subscription_data = {
                "subscription_id": subscription.id,
                "tier": request.tier.lower(),
                "status": subscription.status,
                "current_period_start": datetime.fromtimestamp(
                    subscription.current_period_start
                ),
                "current_period_end": datetime.fromtimestamp(
                    subscription.current_period_end
                ),
                "next_billing_date": datetime.fromtimestamp(
                    subscription.current_period_end
                ),
                "amount": amount,
                "currency": "USD",
            }

        # Save subscription to database
        subscriptions_db[user_id] = subscription_data

        return SubscriptionResponse(**subscription_data)

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment processing error: {e!s}",
        )
    except Exception as e:
        logger.error(f"Subscription creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create subscription",
        )


@router.get("/usage", response_model=UsageResponse)
async def get_usage(current_user: dict = Depends(get_current_user)):
    """
    Get usage information and billing details for the authenticated user.
    """
    user_id = current_user["user_id"]

    try:
        # Get user's subscription
        subscription = subscriptions_db.get(user_id)
        if not subscription:
            tier = SubscriptionTier.FREE
        else:
            tier = SubscriptionTier(subscription["tier"])

        # Create mock usage metrics (replace with real data)
        usage = UsageMetrics(
            user_id=user_id,
            subscription_tier=tier,
            current_period_start=datetime.now().replace(day=1),
            current_period_end=(datetime.now() + timedelta(days=30)).replace(day=1)
            - timedelta(days=1),
            tasks_used_this_month=25,  # Mock data
            total_tokens_used=150000,
            cost_breakdown={"api_calls": 2.50, "storage": 1.00},
            agent_usage={
                "business-analyst": 8,
                "code-reviewer": 6,
                "frontend-developer": 5,
                "data-scientist": 4,
                "security-auditor": 2,
            },
        )

        # Check limits and get recommendations
        limits_check = pricing_manager.check_usage_limits(usage)
        recommendations = pricing_manager.get_upgrade_recommendations(usage)
        billing_summary = pricing_manager.generate_billing_summary(usage)

        return UsageResponse(
            user_id=user_id,
            subscription_tier=tier.value,
            current_usage=limits_check["current_usage"],
            limits=limits_check,
            billing_summary=billing_summary,
            recommendations=recommendations,
        )

    except Exception as e:
        logger.error(f"Usage retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage information",
        )


@router.post("/payment-method")
async def add_payment_method(
    request: PaymentMethodRequest, current_user: dict = Depends(get_current_user)
):
    """
    Add a payment method to the user's account.
    """
    user_id = current_user["user_id"]

    try:
        if not stripe.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment processing not configured",
            )

        # Get or create Stripe customer
        customers = stripe.Customer.list(email=current_user["email"], limit=1)
        if customers.data:
            customer = customers.data[0]
        else:
            customer = stripe.Customer.create(
                email=current_user["email"], metadata={"user_id": user_id}
            )

        # Attach payment method to customer
        stripe.PaymentMethod.attach(request.payment_method_id, customer=customer.id)

        # Set as default if requested
        if request.set_as_default:
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": request.payment_method_id},
            )

        return {"status": "success", "message": "Payment method added successfully"}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe payment method error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment method error: {e!s}",
        )
    except Exception as e:
        logger.error(f"Payment method addition error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add payment method",
        )


@router.post("/cancel")
async def cancel_subscription(current_user: dict = Depends(get_current_user)):
    """
    Cancel the user's subscription.
    """
    user_id = current_user["user_id"]

    try:
        subscription = subscriptions_db.get(user_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active subscription found",
            )

        # Cancel Stripe subscription if it's not free
        if subscription["tier"] != "free" and stripe.api_key:
            stripe.Subscription.delete(subscription["subscription_id"])

        # Update local subscription status
        subscription["status"] = "canceled"
        subscriptions_db[user_id] = subscription

        return {
            "status": "success",
            "message": "Subscription canceled successfully",
            "effective_date": subscription["current_period_end"],
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe cancellation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cancellation error: {e!s}",
        )
    except Exception as e:
        logger.error(f"Subscription cancellation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel subscription",
        )


@router.get("/invoices")
async def get_invoices(current_user: dict = Depends(get_current_user)):
    """
    Get billing history and invoices for the user.
    """
    user_id = current_user["user_id"]

    try:
        if not stripe.api_key:
            return {"invoices": [], "message": "Billing history not available"}

        # Get Stripe customer
        customers = stripe.Customer.list(email=current_user["email"], limit=1)
        if not customers.data:
            return {"invoices": []}

        customer = customers.data[0]

        # Get invoices
        invoices = stripe.Invoice.list(customer=customer.id, limit=12)

        invoice_data = []
        for invoice in invoices.data:
            invoice_data.append(
                {
                    "id": invoice.id,
                    "number": invoice.number,
                    "amount_paid": invoice.amount_paid / 100,  # Convert from cents
                    "currency": invoice.currency.upper(),
                    "status": invoice.status,
                    "created": datetime.fromtimestamp(invoice.created),
                    "period_start": datetime.fromtimestamp(invoice.period_start),
                    "period_end": datetime.fromtimestamp(invoice.period_end),
                    "hosted_invoice_url": invoice.hosted_invoice_url,
                }
            )

        return {"invoices": invoice_data}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe invoice error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice retrieval error: {e!s}",
        )
    except Exception as e:
        logger.error(f"Invoice retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invoices",
        )


# Webhook endpoint for Stripe events
@router.post("/webhook")
async def handle_webhook(request):
    """
    Handle Stripe webhook events for subscription updates.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        if not STRIPE_WEBHOOK_SECRET:
            logger.warning("Stripe webhook secret not configured")
            return {"status": "webhook_secret_not_configured"}

        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )

        # Handle different event types
        if event["type"] == "customer.subscription.updated":
            subscription = event["data"]["object"]
            logger.info(f"Subscription updated: {subscription['id']}")

            # Update local subscription data
            # This would typically update your database

        elif event["type"] == "customer.subscription.deleted":
            subscription = event["data"]["object"]
            logger.info(f"Subscription canceled: {subscription['id']}")

            # Handle subscription cancellation

        elif event["type"] == "invoice.payment_succeeded":
            invoice = event["data"]["object"]
            logger.info(f"Payment succeeded for invoice: {invoice['id']}")

        elif event["type"] == "invoice.payment_failed":
            invoice = event["data"]["object"]
            logger.warning(f"Payment failed for invoice: {invoice['id']}")

        return {"status": "success"}

    except ValueError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


if __name__ == "__main__":
    # Test the billing API
    print("🏷️ Testing Billing API")
    print("=" * 30)

    pm = PricingManager()

    # Test pricing retrieval
    pricing_data = get_pricing_for_api()
    print(f"Available pricing plans: {len(pricing_data['pricing_plans'])}")

    for plan in pricing_data["pricing_plans"]:
        print(f"- {plan['name']}: ${plan['pricing']['monthly']}/month")
        print(f"  Agents: {plan['limits']['total_agents']}")
        print(f"  Tasks: {plan['limits']['max_tasks_per_month'] or 'Unlimited'}")

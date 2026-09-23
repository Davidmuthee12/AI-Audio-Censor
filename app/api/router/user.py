from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from polar_sdk._webhooks import (
    WebhookPayloadAdapter,
    WebhookVerificationError,
)
from standardwebhooks import Webhook

from app.api.dependencies import PolarDep, UserDep, UserServiceDep
from app.api.schemas.user import CheckoutSessionCreate, TokenData, UserCreate, UserRead
from app.config import settings

router = APIRouter(tags=["User"])


@router.get("/me", response_model=UserRead)
async def read_user(user: UserDep):
    return user


@router.post("/user/checkout")
async def create_checkout(body: CheckoutSessionCreate, user: UserDep, polar: PolarDep):
    try:
        checkout = await polar.checkouts.create_async(
            request={
                "products": [settings.POLAR_PRODUCT_ID],
                "customer_email": user.email,
                "external_customer_id": str(user.id),
                "prices": {
                    settings.POLAR_PRODUCT_ID: [
                        {
                            "amount_type": "fixed",
                            # Polar expects amounts in cents, so we multiply by 100
                            "price_amount": int(body.amount * 100),
                        }
                    ]
                },
            }
        )

        return {"url": checkout.url}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.post("/webhooks/polar", include_in_schema=False)
async def handle_polar_webhook(
    request: Request,
    service: UserServiceDep,
):
    try:
        # Get the exact raw request body
        body = await request.body()

        # Verify the webhook directly.
        # This bypasses polar_sdk.validate_event(), whose current
        # implementation incorrectly transforms the whsec_ secret.
        webhook = Webhook(settings.POLAR_WEBHOOK_SECRET)

        data = webhook.verify(
            body,
            request.headers,
        )

        # Validate the payload using Polar's Pydantic adapter
        event = WebhookPayloadAdapter.validate_python(data)

        # Handle the event
        if event.TYPE == "order.created":
            user_id = UUID(event.data.customer.external_id)

            await service.add_credits(
                user_id,
                event.data.subtotal_amount,
            )

        return {"received": True}

    except WebhookVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

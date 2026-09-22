from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from polar_sdk.webhooks import WebhookVerificationError, validate_event

from app.api.dependencies import PolarDep, UserDep, UserServiceDep
from app.api.schemas.user import TokenData, UserCreate, UserRead
from app.config import settings

router = APIRouter(tags=["User"])


@router.post(
    "/signup",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: UserCreate, service: UserServiceDep):
    user = await service.add_user(user_data)
    return user


@router.post("/token", response_model=TokenData)
async def login_user(
    service: UserServiceDep,
    credentials: OAuth2PasswordRequestForm = Depends(),
):
    token = await service.generate_token(
        email=credentials.username,
        password=credentials.password,
    )
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserRead)
async def read_user(user: UserDep):
    return user


@router.post("/user/checkout")
async def create_checkout(user: UserDep, polar: PolarDep):
    try:
        checkout = await polar.checkouts.create_async(
            request={
                "products": [settings.POLAR_PRODUCT_ID],
                "customer_email": user.email,
                "external_customer_id": str(user.id),
            }
        )

        return {"url": checkout.url}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )


@router.post("/webhooks/polar", include_in_schema=False)
async def handle_polar_webhook(request: Request, service: UserServiceDep):
    try:
        event = validate_event(
            body=await request.body(),
            headers=request.headers,
            secret=settings.POLAR_WEBHOOK_SECRET,
        )

        if event.TYPE == "order.created":
            user_id = UUID(event.data.customer.external_id)
            await service.add_credits(user_id)

    except WebhookVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook signature",
        )

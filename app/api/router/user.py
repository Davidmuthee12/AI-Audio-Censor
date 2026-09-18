from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import UserServiceDep
from app.api.schemas.user import TokenData, UserCreate, UserRead

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

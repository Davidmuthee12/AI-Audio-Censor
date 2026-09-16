from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import AudioServiceDep, UserServiceDep
from app.api.schemas import AudioRead, TokenData, UserCreate, UserRead

router = APIRouter()


# Register a new user
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


# Read an audio by ID
@router.get("/audio/{id}", response_model=AudioRead)
async def read_audio(id: UUID, service: AudioServiceDep):
    audio = await service.get_audio(id)

    if not audio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audio not found",
        )

    return audio


# Submit a new audio to censor
@router.post("/audio", response_model=AudioRead)
async def submit_audio(
    audio_file: UploadFile,
    service: AudioServiceDep,
):
    audio = await service.add_audio(audio_file)
    return audio

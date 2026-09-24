from uuid import UUID

from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.exceptions import InsufficientCredits, UserNotFound
from app.database.models import User

password_context = CryptContext(schemes=["argon2"], deprecated="auto")


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, user_data: dict) -> User:
        user = User(
            email=user_data["email"],
            propelauth_id=user_data["user_id"],
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user(self, id: UUID) -> User | None:
        return await self.session.get(User, id)

    async def get_user_by_propelauth_id(self, propelauth_id: str) -> User | None:
        return await self.session.scalar(
            select(User).where(User.propelauth_id == propelauth_id)
        )

    async def deduct_credits(self, user: User, amount: int) -> None:
        if user.credits < amount:
            raise InsufficientCredits()

        user.credits -= amount
        self.session.add(user)
        await self.session.commit()

    async def add_credits(self, user_id: UUID, amount: int) -> None:
        user = await self.get_user(user_id)
        if user is None:
            raise UserNotFound()

        # 1 credit per 1 cent
        user.credits += amount
        self.session.add(user)
        await self.session.commit()

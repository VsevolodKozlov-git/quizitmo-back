from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.db.session import async_session



async def get_user_by_username(username) -> User:
    async with async_session() as db:
        user = (await db.execute(select(User).where(User.username == username))).one()[0]
        return user
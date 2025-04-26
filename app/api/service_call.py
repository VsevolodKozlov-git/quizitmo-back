from fastapi import APIRouter, Depends
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
router = APIRouter(prefix="/service_call")


@router.get("/ping")
async def get_ping():
    return {"msg": "pong"}

@router.get("/test_db")
async def test_db(db: AsyncSession =Depends(get_session)):
    res = (await db.execute(text("select 1"))).scalar()
    return res
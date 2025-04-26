from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from app.db.session import get_session
from app.models.user import User  # Adjust the import according to your project structure
import app.schemas.user as user_schemas
import typing as tp
from app.db.queries import get_user_by_username
from sqlalchemy.exc import NoResultFound
from app.core import auth

router = APIRouter(prefix="/user")






# ------------------Token-----------------
@router.post('/token', status_code=200)
async def create_api_token(
        user_login: tp.Annotated[OAuth2PasswordRequestForm, Depends()]
) -> user_schemas.Token:
    try:
        user_db = await get_user_by_username(user_login.username)
    except NoResultFound:
        raise HTTPException(status_code=400, detail=f'no user with username {user_login.username}')
    print(user_db)
    is_password_correct = auth.verify_password(user_login.password, user_db.password)
    if not is_password_correct:
        raise HTTPException(status_code=400, detail=f'Incorrect password for username: {user_login.username}')

    token = auth.generate_token(user_login.username)
    return user_schemas.Token(access_token=token, token_type='bearer')



@router.get('/', status_code=200)
async def get_current_user(
        user_db: User = Depends(auth.get_current_user)
) -> user_schemas.UserBase:
    return user_schemas.UserBase(username=str(user_db.username))


@router.post('/', status_code=201)
async def create_user(
        user: user_schemas.UserCreate,
        db:AsyncSession=Depends(get_session)
):
    try:
        user_db = await get_user_by_username(user.username)
    except NoResultFound:
        user_db = None
    if user_db is not None:
        raise HTTPException(status_code=400, detail=f'Пользователь с username {user.username} уже существует')
    hashed_password = auth.get_password_hash(user.password)
    user_data = user.model_dump()
    user_data['hashed_password'] = hashed_password
    insert_stmt = (
        insert(User)
        .values(password=hashed_password, username=user.username)
        .returning(User.id_user)
    )
    user_id = (await db.execute(insert_stmt)).scalar()
    await db.commit()
    return {'msg': "Created", 'id': user_id}
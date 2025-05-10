import datetime
import os
import uuid
from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext
from sqlalchemy.exc import NoResultFound

from app.db.queries import get_user_by_username


SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "ebaef943e78aa5ec9fc1a7e25ecff0c772bf70125c671d08ec7924e82e0cc7ce262f99c576fa85620d76b4525f05d6d5958c7ce80e8d4d9532c756f21d49de66bc4e24d65f10d58441af0d6569a9ab1a85c21515f0fd5ac0727e7023af220f2f60b2841968d93597b5a0a28113fb267a5959f52ec5ae4d2d1933d99171c42f52986199600017ecc3c7d27af95554c866b81e007ebd18733c4c7dddaec644498c7866b2fea4bda5feaf0e731540cd77abb773cab407341aaa3b3703e548644c37f51e9e1f917f39612cde9190a588936d857161886948f99464a00e3e06606ddd552e94a10c8c1a6a6d70e73505c733ed0d4dddb7c2b3318dd4cdb7f502bd7eab"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 800000

# hasher setup
crypto_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
# auth scheme setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/token")


def verify_password(provided_password, actual_hash):
    return crypto_context.verify(provided_password, actual_hash)


def get_password_hash(password):
    return crypto_context.hash(password)


def generate_token(username: str) -> str:
    now = datetime.datetime.utcnow()
    expire = now + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # convert to int timestamps (python-jose will accept these cleanly)
    iat = int(now.timestamp())
    exp = int(expire.timestamp())

    to_encode = {
        "sub": username,
        "iat": iat,
        "nbf": iat,
        "exp": exp,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        # note: algorithms is a list
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token format")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    return await get_user_by_token(token)


def get_user_by_token(token):
    token_data = decode_token(token)
    username = token_data['sub']
    try: 
        user = get_user_by_username(username)
    except NoResultFound:
        raise HTTPException(
            status_code=401,
            detail='Invalid token. No such user'
        )
    return user
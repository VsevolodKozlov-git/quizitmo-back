from pydantic import BaseModel, Field
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8, max_length=250)

class UserRead(UserBase):
    id_user: int

    class Config:
        orm_mode = True
        
class Token(BaseModel):
    access_token: str
    token_type: str
    


from pydantic import BaseModel
from typing import Optional

class FriendRequestCreate(BaseModel):
    username: str 

class FriendResponse(BaseModel):
    id: int
    username: str
    status: str
    
    class Config:
        from_attributes = True

class FriendshipUpdate(BaseModel):
    status: str 
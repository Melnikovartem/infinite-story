from datetime import datetime
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    id: str
    email: EmailStr
    username: str
    created_at: datetime = Field(default_factory=datetime.utcnow) 
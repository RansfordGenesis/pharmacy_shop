from pydantic import BaseModel, EmailStr
from datetime import date

class UserBase(BaseModel):
    username: str
    contact: str
    address: str | None
    email: EmailStr | None
    date_of_birth: date | None

class UserCreate(UserBase):
    password: str | None

class UserSchema(UserBase):
    id: int

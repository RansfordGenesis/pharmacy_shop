from typing import Annotated
from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from jose import jwt, JWTError

from pharmacy.database.models.users import User
from pharmacy.database.models.admins import Admin
from pharmacy.dependencies.database import Database
from pharmacy.dependencies.oauth_schemes import user_scheme
from pharmacy.dependencies.oauth_schemes import admin_scheme



def get_authenticator_user(db: Database, token=Depends(user_scheme)) -> User:
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:
        data = dict[str, str] = jwt.decode(
            token=token, key="something", algorithms=["HS256"])
    except JWTError:
        raise token_exception
    
    user_id = int(data["sub"])

    user: User | None = db.get(User, user_id)

    if user is None:
        raise token_exception
    
    return user

def get_authenticator_admin(db: Database, token=Depends(admin_scheme)) -> Admin:
    token_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
    )

    try:
        data = dict[str, str] = jwt.decode(
            token=token, key="something", algorithms=["HS256"])
    except JWTError:
        raise token_exception
    
    admin_id = int(data["sub"])

    admin: Admin | None = db.get(Admin, admin_id)

    if admin is None:
        raise token_exception
    
    return admin

AuthenticatedUser = Annotated[User, Depends(get_authenticator_user)]
AuthenticatedAdmin = Annotated[Admin, Depends(get_authenticator_admin)]
from typing import Annotated
from fastapi import status, Depends
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from pharmacy.database.core import sessionmaker
from pharmacy.database.models.users import User
from pharmacy.database.models.inventories import Inventory
from pharmacy.database.models.admins import Admin



def database_connection():
    with sessionmaker() as connection:
        yield connection

Database = Annotated[Session, Depends(database_connection)]

def get_user_or_404(db: Database, user_id: int) -> User:
    user: User | None = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
        detail="User not found")
    return user

def get_inventory_or_404(db: Database, inventory_id: int) -> User:
    inventory: Inventory | None = db.get(Inventory, inventory_id)
    if inventory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
        detail="Inventory not found")
    return inventory

def get_admin_or_404(db: Database, adnin_id: int) -> User:
    admin: Admin | None = db.get(Admin, adnin_id)
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
        detail="Admin not found")
    return admin

AnnotatedUser = Annotated[User, Depends(get_user_or_404)]
AnnotatedInventory = Annotated[Inventory, Depends(get_inventory_or_404)]
AnnotatedAdmin = Annotated[Admin, Depends(get_admin_or_404)]
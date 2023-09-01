from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from pharmacy.database.models.cart_items import CartItem
from pharmacy.schemas import cart_items
from pharmacy.schemas.cart_items import CartItemCreate
from pharmacy.schemas.tokens import Token
from pharmacy.schemas.users import UserCreate, UserSchema
from pharmacy.database.models.users import User
from pharmacy.database.core import sessionmaker
import sqlalchemy.exc
from sqlalchemy import select

from pharmacy.dependencies.auth import AuthenticatedUser, get_authenticator_admin
from pharmacy.dependencies.database import (
    AnnotatedCartItem, Database, AnnotatedUser, get_inventory_or_404)

from pharmacy.dependencies.jwt import create_token
from pharmacy.security import get_hash, password_matches_hashed
from fastapi.security import OAuth2PasswordRequestForm



router = APIRouter(prefix="/users", tags=["users"])

@router.post("/", response_model=UserSchema)
def create_user(
    user_data: UserCreate,
    db: Database,
) -> User:
    user_data.password = get_hash(user_data.password) 
    user = User(**user_data.model_dump())
    
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except sqlalchemy.exc.IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail="User already exists")
        

@router.get("/", response_model=list[UserSchema])
def get_list_of_users(db: Database) -> list[User]:
    return db.scalar(select(User)).all()


@router.post("/authenticate", response_model=Token)
def login_for_access_token(
    db: Database,
    credentials: OAuth2PasswordRequestForm = Depends(),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
    )

    
    user: User | None = db.scalar(
        select(User).where(User.username == credentials.username))

    if user is None:
        raise credentials_exception

    if not password_matches_hashed(plain=credentials.password, hashed=user.password):
        raise credentials_exception

    data = {"sub": str(user.id)}

    token = create_token(data=data)

    return {"token_type": "bearer", "access_token": token}



@router.get("/current", response_model=UserSchema)
def get_current_user(user: AuthenticatedUser,
    cart_item_data: CartItemCreate,
    db: Database
    ) -> cart_items:
    get_inventory_or_404(db=db, inventory_id=cart_item_data.inventory_id)
    cart_item = CartItem(**cart_item_data.model_dump(), user_id=user.id)
    
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    
    return cart_item



@router.get("/current/cart-items", response_model=list[CartItem])
def get_list_of_cart_items(user: AuthenticatedUser, db: Database) -> list[CartItem]:
    return db.scalar(select(CartItem).where(CartItem.user_id == user.id)).all()



@router.delete("/current/cart-items/{cart_item_id}")
def delete_cart_item(user: AuthenticatedUser, db: Database,
        cart_item: AnnotatedCartItem) -> None:
    db.delete(cart_item)
    db.commit()




@router.post("/current/cart-items", response_model=UserSchema)
def add_item_to_cart(user: AuthenticatedUser, item_id: int, db: Database) -> CartItem:
    user.cart_items.append(item_id)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserSchema,
    dependencies=[Depends(get_authenticator_admin)])

def get_user(user: AnnotatedUser) -> User:
    return user
    

@router.delete("/{user_id}",
    dependencies=[Depends(get_authenticator_admin)])
def delete_user(user: AnnotatedUser, db: Database) -> None:
    with sessionmaker() as db:
        db.delete(user)
        db.commit()

import sqlalchemy.exc
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from pharmacy.database.models.cart_items import CartItem
from pharmacy.database.models.checkouts import Checkout
from pharmacy.database.models.inventories import Inventory
from pharmacy.schemas.cart_items import CartItemCreate, CartItemSchema
from pharmacy.schemas.orders import OrderSchema, OrderItem
from pharmacy.schemas.tokens import Token
from pharmacy.schemas.users import UserCreate, UserSchema
from pharmacy.database.models.users import User
from pharmacy.database.models.orders import Order
from pharmacy.database.core import sessionmaker
from pharmacy.dependencies.auth import AuthenticatedUser, get_authenticator_admin
from pharmacy.dependencies.database import (
    AnnotatedCartItem, Database, AnnotatedUser, get_inventory_or_404)
from pharmacy.enums import OrderStatus

from pharmacy.dependencies.jwt import create_token
from pharmacy.security import get_hash, password_matches_hashed



router = APIRouter(prefix="/users", tags=["Users"])

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
        

@router.get("/", response_model=list[UserSchema],
    dependencies=[Depends(get_authenticator_admin)])
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
def get_current_user(user: AuthenticatedUser) -> User:
    return user


@router.post("/current/cart-items", response_model=UserSchema)
def add_item_to_cart(user: AuthenticatedUser, 
    cart_item_data: CartItemCreate,  db: Database) -> CartItem:
    
    inventory = get_inventory_or_404(db=db, inventory_id=cart_item_data.inventory_id)
    if cart_item_data.quantity > inventory.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail="Quantity is more than available stock")
    
    cart_item = CartItem(**cart_item_data.model_dump(), user_id=user.id)
    
    db.commit(cart_item)
    db.refresh(cart_item)
    return cart_item



@router.get("/current/cart-items", response_model=list[CartItemSchema])
def get_list_of_cart_items(user: AuthenticatedUser, db: Database) -> list[CartItem]:
    return db.scalar(select(CartItem).where(CartItem.user_id == user.id)).all()



@router.post("/current/orders")
def place_order(user: AuthenticatedUser, db: Database) -> None:
    cart_items = db.scalar(select(CartItem).where(CartItem.user_id == user.id)).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, 
        detail="cannot place order with empty cart")
        
    order = Order(status=OrderStatus.PENDING.value, user_id=user.id)
    db.add(order)
    db.commit()
    db.refresh(order)
        
    checkouts: list[Checkout] = []

    for cart_item in cart_items:
        inventory: Inventory | None = db.get(Inventory, cart_item.inventory_id)

        if inventory is None:
            continue

        if cart_item.quantity > inventory.quantity:
            db.delete(order)
            db.commit()

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"not enough items in stock for {inventory.name}."
                    f"Tried to order: {cart_item.quantity}"
                    f"In stock: {inventory.quantity}"
                ),
            )

        checkout = Checkout(
            order_id=order.id,
            cart_item_id=cart_item.id,
            sub_total=cart_item.quantity * inventory.price,
        )

        checkouts.append(checkout)
        inventory.quantity -= cart_item.quantity

    db.add_all(checkouts)
    db.commit()
    
    

@router.get("/current/orders", response_model=list[OrderSchema])
def get_list_of_orders(user: AuthenticatedUser, db: Database):
    db_orders = db.scalars(select(Order).where(Order.user_id == user.id)).all()

    orders: list[OrderSchema] = []

    for db_order in db_orders:
        order = OrderSchema(id=db_order.id, status=db_order.status)

        checkouts = db.scalars(
            select(Checkout).where(Checkout.order_id == db_order.id)
        ).all()

        for checkout in checkouts:
            order.total += checkout.sub_total

            cart_item = db.scalar(
                select(CartItem).where(CartItem.id == checkout.cart_item_id)
            )

            inventory = db.scalar(
                select(Inventory).where(Inventory.id == cart_item.inventory_id)
            )

            order_item = OrderItem(
                quantity=cart_item.quantity,
                name=inventory.name,
                sub_total=checkout.sub_total,
            )

            order.order_items.append(order_item)

        order.user = user
        orders.append(order)

    return orders



@router.delete("/current/cart-items/{cart_item_id}")
def delete_cart_item(user: AuthenticatedUser, db: Database,
        cart_item: AnnotatedCartItem) -> None:
    db.delete(cart_item)
    db.commit()



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

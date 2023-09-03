from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from pharmacy.database.core import Base

class Checkout(Base):
    __tablename__ = "checkouts"

    cart_item_id: Mapped[int] = mapped_column(ForeignKey("cart_item.id"), 
        primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), primary_key=True)
    subtotal: Mapped[float] = mapped_column(nullable=False)
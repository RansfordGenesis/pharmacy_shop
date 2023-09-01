from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from pharmacy.database.core import Base

class Checkout(Base):
    __tablename__ = "checkouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_item_id: Mapped[int] = mapped_column(ForeignKey("cart_item.id"), 
        nullable=False)
    order_id: Mapped[int] = mapped_column(ForeignKey("user.id", nullable=False))
    subtotal: Mapped[float] = mapped_column(nullable=False)
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from pharmacy.database.core import Base

class CartItem(Base):
    __tablename__ = "cart_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory.id"), 
        nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id", nullable=False))
    
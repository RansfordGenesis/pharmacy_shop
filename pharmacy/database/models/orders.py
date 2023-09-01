from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from pharmacy.database.core import Base

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    cart_item_id: Mapped[int] = mapped_column(ForeignKey("cart_item.id"), 
        nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from pharmacy.database.core import Base

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    status: Mapped[str] = mapped_column(String, nullable=False)
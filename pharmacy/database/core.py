from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


engine = create_engine(
    "sqlite:///pharmacy.shop", 
    echo=True,
    connect_args={"check_same_thread": False}
    )

SessionMaker = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    autocommit=False
    )

class Base(DeclarativeBase):
    pass


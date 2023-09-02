from contextlib import asynccontextmanager
from fastapi import FastAPI
from pharmacy.database.core import Base, engine
from pharmacy.routers import users, inventories, admins

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
        

app = FastAPI(lifespan=lifespan)
app.include_router(inventories.router)
app.include_router(users.router)
app.include_router(admins.router)


@app.get("/ping")
def pong():
    return {"message": "pong"}

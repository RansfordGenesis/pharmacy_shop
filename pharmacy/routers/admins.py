import sqlalchemy.exc
from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from fastapi.exceptions import HTTPException 

from pharmacy.dependencies.auth import AuthenticatedAdmin
from pharmacy.security import get_hash, password_matches_hashed
from pharmacy.database.models.admins import Admin
from pharmacy.dependencies.jwt import create_token
from pharmacy.schemas.tokens import Token
from pharmacy.dependencies.database import Database, AnnotatedAdmin
from pharmacy.schemas.admins import AdminSchema, AdminCreate

router = APIRouter(prefix="/admins", tags=["admins"])

@router.post("/", response_model=AdminSchema)
def create_admins(admin_data: AdminCreate, db: Database) -> Admin:
    admin_data.password = get_hash(admin_data.password)
    admin = Admin(**admin_data.model_dump())

    try:
        db.add(admin)
        db.commit()
        db.refresh(admin)

        return admin
    except sqlalchemy.exc.IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="admin already exists")

@router.get("/", response_model=list[AdminSchema])
def get_list_of_admins(db: Database):
    return db.scalars(select(Admin)).all()

@router.post("/authenticate", response_model=Token)
def login_for_access_token(
    db: Database, credentials: OAuth2PasswordRequestForm = Depends()):
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, 
    detail="incorrect username or password",)

    admin: Admin | None = db.scalar(select(Admin).where(
        Admin.username == credentials.username))
    
    if admin is None:
        raise credentials_exception
    
    if not password_matches_hashed(plain=credentials.password, hashed=admin.password):
        raise credentials_exception

    data = {"sub": str(admin.id)}

    token = create_token(data=data)

    return {"token_type": "bearer", "token": token}

@router.get("/current", response_model=AdminSchema)
def get_current_admin(admin: AuthenticatedAdmin) -> Admin:
    return admin

@router.get("/{admin_id}", response_model=AdminSchema)
def get_admin(admin: AnnotatedAdmin):
    return admin

@router.delete("/{admin_id}")
def delete_admin(admin: AnnotatedAdmin, db: Database):
    db.delete(admin)
    db.commit()
from uuid import uuid4
from datetime import datetime, timedelta
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from .models import User, Token

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
TOKEN_EXPIRE_MINUTES = 60

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user

def create_access_token(db: Session, user_id: int) -> str:
    token_value = uuid4().hex
    expires_at = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)

    db_token = Token(
        token=token_value,
        user_id=user_id,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token.token
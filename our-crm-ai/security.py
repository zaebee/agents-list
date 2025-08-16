from datetime import datetime, timedelta
import os

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt
from pydantic import BaseModel

from database import get_db_connection, verify_password

SECRET_KEY = os.getenv("SECRET_KEY", "development-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.PyJWTError:
        raise credentials_exception
    return token_data


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = verify_token(token, credentials_exception)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, username, email, full_name, role FROM users WHERE username = ?",
            (token_data.username,),
        )
        user_row = cursor.fetchone()
        if user_row is None:
            raise credentials_exception

        # Convert SQLite Row to dict for proper serialization
        user = {
            "id": user_row["id"],
            "username": user_row["username"],
            "email": user_row.get("email"),
            "full_name": user_row.get("full_name"),
            "role": user_row.get("role", "user"),
            "disabled": False
        }
        return user


def authenticate_user(username, password, db_path="business_analytics.db"):
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        if not user_row:
            return False
        if not verify_password(password, user_row["password_hash"]):
            return False

        # Convert SQLite Row to dict for proper serialization
        user = {
            "id": user_row["id"],
            "username": user_row["username"],
            "email": user_row.get("email"),
            "full_name": user_row.get("full_name"),
            "role": user_row.get("role", "user"),
            "disabled": False
        }
        return user

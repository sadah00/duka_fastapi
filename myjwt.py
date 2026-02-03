from datetime import datetime, timedelta, timezone
from typing import Annotated
from models import User, SessionLocal
from jsonmap import TokenData
from sqlalchemy import select

#import jwt
from jose import JWTError, jwt
from fastapi import Depends, FastAPI, HTTPException, Security, status
from fastapi.security import (
    HTTPBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()

#from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()
SECRET_KEY = "3q45wgte67u8l;0-i'[plokiujnyhbtgvrfdefrghtyulkoiujyhtgrfd]"

security = HTTPBearer()
    


def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_hash.hash(password)


""" async def get_user(email: str):
    user= await SessionLocal.execute(select(User).where(User.email==user.email)).scalar_one_or_none()
    return user
 """
""" if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict) """

def get_user(email: str):
    return SessionLocal.execute(
        select(User).where(User.email == email)
    ).scalar_one_or_none()




def authenticate_user(email: str, password: str):
    user = get_user(email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# async def get_current_user(
#     security_scopes: SecurityScopes, token: Annotated[str, Depends(security)]
# ):
#     if security_scopes.scopes:
#         authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
#     else:
#         authenticate_value = "Bearer"
#     credentials_exception = HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Could not validate credentials",
#         headers={"WWW-Authenticate": authenticate_value},
#     )
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email = payload.get("sub")
#         if email is None:
#             raise credentials_exception
#         scope: str = payload.get("scope", "")
#         token_scopes = scope.split(" ")
#         token_data = TokenData(scopes=token_scopes, email=email)
#     except Exception:
#         raise credentials_exception
#     user = get_user(token_data.email)
#     if user is None:
#         raise credentials_exception
#     for scope in security_scopes.scopes:
#         if scope not in token_data.scopes:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Not enough permissions",
#                 headers={"WWW-Authenticate": authenticate_value},
#             )
#     return user

# def get_current_user(
#     credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)]
# ):
#     token = credentials.credentials  # <-- RAW token from Swagger

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         email: str = payload.get("sub")
#         if email is None:
#             raise HTTPException(status_code=401, detail="Invalid token")
#     except JWTError:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     user = get_user(email=email)
#     if user is None:
#         raise HTTPException(status_code=401, detail="User not found")

#     return user

# def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(security)
# ):
#     token = credentials.credentials

#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#     except jwt.PyJWTError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid token"
#         )

#     email = payload.get("email")
#     if not email:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Email not found in token"
#         )

#     return email

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    email = payload.get("email") or payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    return email

async def get_current_active_user(
    current_user: Annotated[User, Security(get_current_user, scopes=["me"])],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
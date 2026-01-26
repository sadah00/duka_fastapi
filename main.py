from typing import Union, List, Annotated
from fastapi import FastAPI, Depends,HTTPException, status
from sqlalchemy.orm import Session,selectinload
from models import Base,engine,SessionLocal
from sqlalchemy import select
from jsonmap import ProductGetMap, ProductPostMap, SaleGetMap, SalePostMap, UserPostRegister, UserPostLogin
from models import Product,Sale,User
from jwt import create_access_token, authenticate_user,get_password_hash,verify_password
from datetime import timedelta
from jsonmap import Token
from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
    SecurityScopes,
)

app = FastAPI()

# Create tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"Duka FastAPI": "Version 1.0"}

@app.post("/register", response_model=Token)
def register_user(user: UserPostRegister):
    # Check if email is already registered
    if SessionLocal.execute(
        select(User).where(User.email == user.email)
    ).scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = get_password_hash(user.password)

    # Create User model object
    model_obj = User(
        email=user.email,
        username=user.username,
        password=hashed_password
    )

    # Save to database
    SessionLocal.add(model_obj)
    SessionLocal.commit()

    # Create access token (default scopes empty)
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user.email,  # store email in JWT
            "scope": "",        # default scopes
        },
        expires_delta=access_token_expires
    )

    # Return the token
    return Token(access_token=access_token, token_type="bearer")

@app.post("/login", response_model=Token)
def login_user(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user.email,
            "scope": " ".join(form_data.scopes),
        },
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@app.get("/products", response_model=List[ProductGetMap])
def get_products():
    products=select(Product)
    return SessionLocal.scalars(products)

@app.post("/products", response_model=ProductGetMap)
def create_product(json_product_obj:ProductPostMap):
    model_obj=Product(
        name=json_product_obj.name,
        buying_price=json_product_obj.buying_price,
        selling_price=json_product_obj.selling_price
    )
    SessionLocal.add(model_obj)
    SessionLocal.commit()
    return model_obj

@app.get("/sales",response_model=List[SaleGetMap])
def get_sales():
    sales=select(Sale).join(Sale.product)
    return SessionLocal.scalars(sales)

@app.post("/sales", response_model=SaleGetMap)
def create_sales(json_sales_obj:SalePostMap):
    model_obj=Sale(
        product_id=json_sales_obj.product_id,
        quantity=json_sales_obj.quantity
    )
    SessionLocal.add(model_obj)
    SessionLocal.commit()
    return model_obj
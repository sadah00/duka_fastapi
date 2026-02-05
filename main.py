from typing import Union, List, Annotated
from fastapi import FastAPI, Depends,HTTPException, status
from sqlalchemy.orm import Session,selectinload
from models import Base,engine,SessionLocal
from sqlalchemy import select,func
from jsonmap import ProductGetMap, ProductPostMap, SaleGetMap, SalePostMap, UserPostRegister, UserPostLogin ,PurchaseGetMap, PurchasePostMap,SalesPerProduct,StockPerProduct,ProfitPerProduct,ProfitPerDay,ProfitPerProductPerDay
from models import Product,Sale,User,Purchase
from myjwt import create_access_token, authenticate_user,get_password_hash,verify_password,security,get_current_user
from datetime import timedelta
from jsonmap import Token
from fastapi.security import (
    OAuth2PasswordRequestForm,
    SecurityScopes,
)

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()

app = FastAPI()

# Create tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"Duka FastAPI": "Version 1.0"}

# ---------------- LOGIN (OAUTH2 – SWAGGER) ----------------
@app.post("/token", tags=["auth"])
def login_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.email, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(user.email)
    return {
        "access_token": token,
        "token_type": "bearer",
    }

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
        full_name=user.full_name,
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
def login_user(user_json:UserPostLogin):
    user = authenticate_user(user_json.email, user_json.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={
            "sub": user_json.email
            # "scope": " ".join(user_json.scopes),
        },
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type="bearer")


@app.get("/products", response_model=List[ProductGetMap])
def get_products(
    current_user: Annotated[User, Depends(security)]
):
    print(f"Current user---------------------: {current_user}")
    products=select(Product)
    return SessionLocal.scalars(products)

@app.post("/products", response_model=ProductGetMap)
def create_product(
    current_user: Annotated[User, Depends(security)],
    json_product_obj:ProductPostMap
    ):

    model_obj=Product(
        name=json_product_obj.name,
        buying_price=json_product_obj.buying_price,
        selling_price=json_product_obj.selling_price
    )
    SessionLocal.add(model_obj)
    SessionLocal.commit()
    return model_obj

@app.get("/sales",response_model=List[SaleGetMap])
def get_sales(
    current_user: Annotated[User, Depends(security)]
    ):
    print(f"Current user---------------------: {current_user}")
    
    sales=select(Sale).join(Sale.product)
    return SessionLocal.scalars(sales)

@app.post("/sales", response_model=SaleGetMap)
def create_sales(
    current_user: Annotated[User, Depends(security)],
    json_sales_obj:SalePostMap
    ):
    model_obj=Sale(
        product_id=json_sales_obj.product_id,
        quantity=json_sales_obj.quantity
    )
    SessionLocal.add(model_obj)
    SessionLocal.commit()
    return model_obj

@app.post("/purchases", response_model=PurchaseGetMap)
def create_purchase(
    current_user: Annotated[User, Depends(security)],
    json_purchase_obj:PurchasePostMap
    ):
    model_obj=Purchase(
        product_id=json_purchase_obj.product_id,
        stock_quantity=json_purchase_obj.stock_quantity,
        created_at=json_purchase_obj.created_at
    )
    SessionLocal.add(model_obj)
    SessionLocal.commit()
    return model_obj

@app.get("/purchases", response_model=List[PurchaseGetMap])
def get_purchases(
    current_user: Annotated[User, Depends(security)]
):
    print(f"Current user---------------------: {current_user}")
    purchases=select(Purchase)
    return SessionLocal.scalars(purchases)


# 🔹 Sales per product
@app.get("/dashboard/sales-per-product", response_model=list[SalesPerProduct])
def sales_per_product(
    current_user: Annotated[User, Depends(security)]
):
    sales_data = (
        SessionLocal.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(Sale.quantity).label("total_quantity_sold"),
            func.sum(Sale.quantity * Product.selling_price).label("total_sales_amount")
        )
        .join(Sale, Product.id == Sale.product_id)
        .group_by(Product.id, Product.name)
        .all()
    )

    result = [
        SalesPerProduct(
            product_id=row.product_id,
            product_name=row.product_name,
            total_quantity_sold=row.total_quantity_sold,
            total_sales_amount=row.total_sales_amount
        )
        for row in sales_data
    ]

    return result
    

@app.get("/dashboard/remaining-stock-per-product",response_model=List[StockPerProduct])
def get_stock_per_product(
     current_user: Annotated[User, Depends(get_current_user)]
):
    sales_subquery = (
        select(
            Sale.product_id,
            func.coalesce(func.sum(Sale.quantity), 0).label("total_sold")
        ).group_by(Sale.product_id)
        .subquery()
    )

    purchases_subquery = (
        select(
            Purchase.product_id,
            func.coalesce(func.sum(Purchase.stock_quantity), 0).label("total_purchased")
        ).group_by(Purchase.product_id)
        .subquery()
    )

    stock_data = SessionLocal.execute(
        select(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            (func.coalesce(purchases_subquery.c.total_purchased, 0) - func.coalesce(sales_subquery.c.total_sold, 0)).label("remaining_stock")
        ).outerjoin(sales_subquery, Product.id == sales_subquery.c.product_id
        ).outerjoin(purchases_subquery, Product.id == purchases_subquery.c.product_id)
    ).all()

    result = [
        StockPerProduct(
            product_id=row.product_id,
            product_name=row.product_name,
            remaining_stock=row.remaining_stock
        )
        for row in stock_data
    ]

    return result

@app.get("/dashboard/profit-per-product", response_model=list[ProfitPerProduct])
def profit_per_product(
    current_user: Annotated[User, Depends(security)]
):
    profit_data = (
        SessionLocal.query(
            Product.id.label("product_id"),
            Product.name.label("product_name"),
            func.sum(Sale.quantity * (Product.selling_price - Product.buying_price)).label("total_profit")
        )
        .join(Sale, Product.id == Sale.product_id)
        .group_by(Product.id, Product.name)
        .all()
    )

    result = [
        ProfitPerProduct(
            product_id=row.product_id,
            product_name=row.product_name,
            total_profit=row.total_profit
        )
        for row in profit_data
    ]

    return result

@app.get("/dashboard/profit-per-day",response_model=List[ProfitPerDay])
def get_profit_per_day(
     current_user: Annotated[User, Depends(get_current_user)]
):
    profit_data = SessionLocal.execute(
        select(
            func.date(Sale.created_at).label("date"),
            func.sum(Sale.quantity * (Product.selling_price - Product.buying_price)).label("total_profit")
        ).join(Product, Sale.product_id == Product.id
        ).group_by(func.date(Sale.created_at))
    ).all()

    result = [
        ProfitPerDay(
            date=row.date,
            total_profit=row.total_profit
        )
        for row in profit_data
    ]

    return result

@app.get("/dashboard/profit-per-product-per-day",response_model=List[ProfitPerProductPerDay])
def get_profit_per_product_per_day(
     current_user: Annotated[User, Depends(get_current_user)]
):
    profit_data = SessionLocal.execute(
        select(
            func.date(Sale.created_at).label("date"),
            Sale.product_id,
            Product.name.label("product_name"),
            func.sum(Sale.quantity * (Product.selling_price - Product.buying_price)).label("total_profit")
        ).join(Product, Sale.product_id == Product.id
        ).group_by(func.date(Sale.created_at), Sale.product_id, Product.name)
    ).all()

    result = [
        ProfitPerProductPerDay(
            date=row.date,
            product_id=row.product_id,
            product_name=row.product_name,
            total_profit=row.total_profit
        )
        for row in profit_data
    ]

    return result
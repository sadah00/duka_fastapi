from pydantic import BaseModel
from datetime import datetime

class UserPostRegister(BaseModel):
    email: str
    full_name: str 
    password: str

class UserPostLogin(BaseModel):
    email: str
    password: str

class ProductPostMap(BaseModel):
    name: str
    buying_price: float
    selling_price: float

class ProductGetMap(ProductPostMap):
    id: int

 
class SalePostMap(BaseModel):
    product_id: int
    quantity: int

class SaleGetMap(SalePostMap):
    id: int
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    scopes: list[str] = []

class PurchasePostMap(BaseModel):
    product_id: int
    stock_quantity: int
    created_at: datetime

class PurchaseGetMap(PurchasePostMap):
    id: int

class SalesPerProduct(BaseModel):
    data: list[int]
    labels: list[str]

class StockPerProduct(BaseModel):
    product_id: int
    product_name: str
    remaining_stock: int

class ProfitPerProduct(BaseModel):
    product_id: int
    product_name: str
    total_profit: float

class ProfitPerDay(BaseModel):
    date: datetime
    total_profit: float

class ProfitPerProductPerDay(BaseModel):
    date: datetime
    product_id: int
    product_name: str
    total_profit: float



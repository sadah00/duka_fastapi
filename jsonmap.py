from pydantic import BaseModel
from datetime import datetime

class UserPostRegister(BaseModel):
    email: str
    username: str 
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



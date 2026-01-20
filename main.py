from typing import Union, List
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import Base,engine,SessionLocal
from sqlalchemy import select
from jsonmap import ProductGetMap, ProductPostMap, SaleGetMap, SalePostMap
from models import Product,Sale

app = FastAPI()

# Create tables on startup
@app.on_event("startup")
def create_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def read_root():
    return {"Duka FastAPI": "Version 1.0"}


@app.get("/products", response_model=List[ProductGetMap])
def get_products():
    products=select(Product)
    return SessionLocal.scalars(products)

@app.get("/sales",response_model=List[SaleGetMap])
def get_sales():
    sales=select(Sale).join(Sale.product)
    return SessionLocal.scalars(sales)

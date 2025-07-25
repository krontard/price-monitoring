from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.models.product import Product as ProductModel


router = APIRouter()

@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = ProductModel(
        name=product.name,
        description=product.description,
         amazon_url=str(product.amazon_url) if product.amazon_url else None,
        wildberries_url=str(product.wildberries_url) if product.wildberries_url else None,
        ozon_url=str(product.ozon_url) if product.ozon_url else None,
  
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    #здесь будет вывод сервиса поиска товаров на маркетплейсах
    return db_product

@router.get("/", response_model=List[Product])
def read_product(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(ProductModel).offset(skip).limit(limit).all()
    return products

@router.get("/{product_id}", response_model=Product)
def read_products(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:  
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )
    return db_product

@router.put("/{product_id}", response_model=Product)
def update_product(product_id: int, product: ProductUpdate, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    update_data = product.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ['amazon_url', 'wildberries_url', 'ozon_url'] and value is not None:
            value = str(value)
        setattr(db_product, field, value)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id:int, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )
    db.delete(db_product)
    db.commit()
    return None
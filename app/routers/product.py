from fastapi import Response, status, HTTPException, Depends, APIRouter
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix='/products')

@router.get("/all", response_model=List[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db), search: Optional[str] = ''):
    all_products = db.query(models.Product).filter(models.Product.name.contains(search)).all()
    return all_products

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    all_categories = db.query(models.Product.category).distinct().all()
    return all_categories

@router.get("/admin", response_model=List[schemas.ProductAdmin])
def get_products_admin(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    all_products = db.query(models.Product).all()
    return all_products
    
@router.post("", status_code=status.HTTP_201_CREATED, response_model=schemas.ProductResponse)
def add_product(product: schemas.Product, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    return new_product

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(id: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    deleted_item = db.query(models.Product).filter(models.Product.id == id)
    if deleted_item.first() == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"item wth id: {id} does not exist")
    deleted_item.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}")
def update_product(id: int, product: schemas.ProductAdmin, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    update_query = db.query(models.Product).filter(models.Product.id == id)
    updated_product = update_query.first()
    if updated_product == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"product with id: {id} does not exist")
    update_query.update(product.dict(), synchronize_session=False)
    db.commit()
    return {"msg": "Update successfully"}
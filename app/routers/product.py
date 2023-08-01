from fastapi import Response, status, HTTPException, Depends, APIRouter, UploadFile
from fastapi.responses import FileResponse
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
import aiofiles
import os
from ..database import get_db
from .. import models, schemas
from ..config import settings

router = APIRouter(prefix='/products')

@router.get("/all", response_model=List[schemas.ProductResponse])
def get_products(db: Session = Depends(get_db), search: Optional[str] = ''):
    all_products = db.query(models.Product).filter(models.Product.name.contains(search)).all()
    return all_products

@router.get("/categories", response_model=List[schemas.CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    all_categories = db.query(models.Product.category).distinct().all()
    return all_categories

@router.get("/image/{id}", response_class=FileResponse)
async def get_image_by_product_id(id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == id).first()
    if product.image:
        return os.path.join(settings.image_path, product.image)
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Image does not exist")

@router.get("/admin", response_model=List[schemas.ProductAdminResponse])
def get_products_admin(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    all_products = db.query(models.Product).all()
    return all_products
    
@router.post("", status_code=status.HTTP_201_CREATED)
def add_product(product: schemas.ProductAdminCreate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    return {"msg": "Item was add successfully"}

@router.post("/image")
async def upload_image(file: UploadFile | None = None, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    if not file:
        return {"msg": "No upload file sent"}
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    async with aiofiles.open(os.path.join(settings.image_path, file.filename), 'wb') as out_file:
        while content := await file.read(1024):  # async read chunk
            await out_file.write(content)  # async write chunk
    return {"msg": "Image successfully uploaded"}

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(id: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or user.is_admin == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    
    delete_query = db.query(models.Product).filter(models.Product.id == id)
    item_delete = delete_query.first()
    if item_delete == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"item wth id: {id} does not exist")
    
    if item_delete.image:
        os.remove(os.path.join(settings.image_path, item_delete.image))

    delete_query.delete(synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.put("/{id}")
def update_product(id: int, product: schemas.ProductAdminUpdate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
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
    update_query.update(product.dict(exclude_unset=True), synchronize_session=False)
    db.commit()
    return {"msg": "Update successfully"}
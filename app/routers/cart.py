from fastapi import status, HTTPException, Depends, APIRouter
from typing import List
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix='/cart')

@router.get("/", response_model=List[schemas.CartItem])
def get_cart(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    cart_items = db.query(models.CartItem).join(models.Product, models.CartItem.user_id == user_id)
    response = []
    for cart_item in cart_items:
        response.append(schemas.CartItem(id=cart_item.product_id, 
                                         name=cart_item.product.name,
                                         price=cart_item.product.price,
                                         inventory=cart_item.product.inventory,
                                         size=cart_item.product.size,
                                         category=cart_item.product.category,
                                         image=cart_item.product.image,
                                         quantity=cart_item.quantity,
                                         synced=cart_item.synced))
    return response

@router.put("/")
def get_cart(cart: schemas.UserCart, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    for item in cart.cart:
        if item.user_id == user_id and not item.synced:
            # user modified cart item in front end, update in db
            update_query = db.query(models.CartItem).filter(models.CartItem.user_id == item.user_id and models.CartItem.product_id == item.product_id)
            updated_item = update_query.first()
            if updated_item == None:
                # new item
                item.synced = True
                new_item = models.CartItem(**item.dict())
                db.add(new_item)
            else:
                if item.quantity == 0:
                    update_query.delete(synchronize_session=False)
                else:
                    item.synced = True
                    update_query.update(item.dict(), synchronize_session=False)
    db.commit()

    return {"msg":"Cart is updated successfully"}
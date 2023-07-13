from fastapi import status, HTTPException, Depends, APIRouter
from typing import List
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
from ..database import get_db
from .. import models, schemas

router = APIRouter(prefix='/cart')

@router.get("", response_model=List[schemas.CartItem])
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
                                         synced=True))
    return response

@router.put("", response_model=List[schemas.CartItem])
def update_cart(cart: schemas.UserCart, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    if not cart.items:
        # empty cart
        update_query = db.query(models.CartItem).filter(models.CartItem.user_id == user_id)
        update_query.delete(synchronize_session=False)
    for item in cart.items:
        if not item.synced:
            # user modified cart item in front end, update in db
            update_query = db.query(models.CartItem).filter(models.CartItem.user_id == user_id, models.CartItem.product_id == item.id)
            old_item = update_query.first()
            item.synced = True
            if old_item == None:
                # new item
                new_item = models.CartItem(user_id=user_id,
                                           product_id=item.id,
                                           quantity=item.quantity)
                db.add(new_item)
            else:
                if item.quantity == 0:
                    update_query.delete(synchronize_session=False)
                    cart.items.remove(item)
                else:
                    update_query.update({'quantity': item.quantity}, synchronize_session=False)
    db.commit()
    return cart.items

def calculate_cart_subtotal(cart_items:List[schemas.CartItem], db: Session = Depends(get_db)):
    subtotal = 0
    for item in cart_items:
        item_price = db.query(models.Product).filter(models.Product.id == item.id).first().price
        subtotal += item_price * item.quantity
    return subtotal
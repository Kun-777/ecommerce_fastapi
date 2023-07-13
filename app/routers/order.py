from fastapi import status, HTTPException, Depends, APIRouter
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
import datetime
from ..database import get_db
from .. import models, schemas
from ..config import settings
from .cart import calculate_cart_subtotal
import stripe

router = APIRouter(prefix='/order')

stripe.api_key = 'sk_test_51IKbDnFQkLBQJ2dHHlT7camnvQdyNDyLE4u4Tqtw7WScJJ3B0c8qfttUE4Fimhdblk6Z69vMC0itPT0y1KDaPNW000qIxA1l6P'

@router.post("/create")
def create_order(cart: schemas.UserCart, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    clean_expired_orders(db)
    # calculate total
    if cart.order_type == 'pick up':
        total = calculate_cart_subtotal(cart.items, db) * (1 + settings.tax_rate)
    else:
        total = (calculate_cart_subtotal(cart.items, db) + settings.delivery_fee) * (1 + settings.tax_rate)

    Authorize.jwt_optional()
    user_id = Authorize.get_jwt_subject()

    if user_id:
        new_order = models.Order(user_id=user_id, total=total, order_type=cart.order_type, status='created')
        db.add(new_order)
    else:
        new_order = models.Order(total=total, order_type=cart.order_type, status='created')
        db.add(new_order)
    db.commit()

    for item in cart.items:
        new_order_item = models.OrderItem(order_id=new_order.id, product_id=item.id, quantity=item.quantity)
        db.add(new_order_item)
    
    db.commit()
    return {'order_id': new_order.id}

@router.post('/create-payment-intent')
def create_payment(order: schemas.OrderCreate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    clean_expired_orders(db)
    # calculate total
    if order.order_type == 'pick up':
        total = calculate_cart_subtotal(order.items, db) * (1 + settings.tax_rate)
    else:
        total = (calculate_cart_subtotal(order.items, db) + settings.delivery_fee) * (1 + settings.tax_rate)
    total = round(total, 2)
    # add new order to the database
    Authorize.jwt_optional()
    user_id = Authorize.get_jwt_subject()

    if user_id:
        new_order = models.Order(user_id=user_id, total=total, order_type=order.order_type,
                                 first_name=order.first_name,
                                 last_name=order.last_name,
                                 email=order.email,
                                 phone=order.phone,
                                 address_line_1=order.address_line_1,
                                 address_line_2=order.address_line_2,
                                 city=order.city,
                                 state=order.state,
                                 zip_code=order.zip_code,
                                 status='created')
        db.add(new_order)
    else:
        new_order = models.Order(total=total, order_type=order.order_type, 
                                 first_name=order.first_name,
                                 last_name=order.last_name,
                                 email=order.email,
                                 phone=order.phone,
                                 address_line_1=order.address_line_1,
                                 address_line_2=order.address_line_2,
                                 city=order.city,
                                 state=order.state,
                                 zip_code=order.zip_code,
                                 status='created')
        db.add(new_order)
    db.commit()

    for item in order.items:
        new_order_item = models.OrderItem(order_id=new_order.id, product_id=item.id, quantity=item.quantity)
        db.add(new_order_item)
    db.commit()

    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=total,
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
        )
        return {
            'clientSecret': intent['client_secret'], 'orderId': new_order.id, 'total': total
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))
    
@router.put('/place')
def place_order(order_id, db: Session = Depends(get_db)):
    update_query = db.query(models.Order).filter(models.Order.id == order_id)
    old_order = update_query.first()
    if old_order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="session expired or order does not exist")
    update_query.update({'status': 'placed'})
    db.commit()
    return {"msg": "Order is placed successfully"}

@router.put('/confirm')
def confirm_payment(order_id, db: Session = Depends(get_db)):
    update_query = db.query(models.Order).filter(models.Order.id == order_id)
    old_order = update_query.first()
    if old_order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="order does not exist")
    customer_reference = datetime.datetime.today().strftime('%m%d%Y') + str(order_id)
    update_query.update({'status': 'confirmed'})
    db.commit()
    return {"msg": "Payment is confirmed"}
    
def clean_expired_orders(db: Session = Depends(get_db)):
    current_time = datetime.datetime.now()
    fifteen_min_ago = current_time - datetime.timedelta(minutes=15)
    clean_query = db.query(models.Order).filter(models.Order.created_at < fifteen_min_ago, models.Order.status == 'created')
    clean_query.delete(synchronize_session=False)
    db.commit()


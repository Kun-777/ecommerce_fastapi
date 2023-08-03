from fastapi import status, HTTPException, Depends, APIRouter
from typing import List
from sqlalchemy.orm import Session
from fastapi_jwt_auth import AuthJWT
import datetime
from ..database import get_db
from .. import models, schemas
from ..config import settings
from ..utils import send_txt_message, check_addr_within_range
from .cart import calculate_cart_subtotal
import stripe

router = APIRouter(prefix='/order')

stripe.api_key = settings.stripe_api_key

@router.post('/create-payment-intent')
def create_payment(order: schemas.OrderCreate, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    clean_expired_orders(db)
    # calculate total
    subtotal = calculate_cart_subtotal(order.items, db)
    if order.order_type == 'pick up':
        total = subtotal * (1 + settings.tax_rate)
    else:
        total = (subtotal + settings.delivery_fee) * (1 + settings.tax_rate) + order.tip
    total = round(total, 2)
    # add new order to the database
    Authorize.jwt_optional()
    user_id = Authorize.get_jwt_subject()

    if user_id:
        new_order = models.Order(user_id=user_id, 
                                 subtotal=subtotal,
                                 total=total, 
                                 order_type=order.order_type,
                                 first_name=order.first_name,
                                 last_name=order.last_name,
                                 email=order.email,
                                 phone=order.phone,
                                 address_line_1=order.address_line_1,
                                 address_line_2=order.address_line_2,
                                 city=order.city,
                                 state=order.state,
                                 zip_code=order.zip_code,
                                 schedule=order.schedule,
                                 tip=round(order.tip, 2),
                                 status='created')
        db.add(new_order)
    else:
        new_order = models.Order(subtotal=subtotal, 
                                 total=total,
                                 order_type=order.order_type, 
                                 first_name=order.first_name,
                                 last_name=order.last_name,
                                 email=order.email,
                                 phone=order.phone,
                                 address_line_1=order.address_line_1,
                                 address_line_2=order.address_line_2,
                                 city=order.city,
                                 state=order.state,
                                 zip_code=order.zip_code,
                                 schedule=order.schedule,
                                 tip=round(order.tip, 2),
                                 status='created')
        db.add(new_order)
    db.commit()
    customer_reference = datetime.datetime.today().strftime('%m%d%Y') + str(new_order.id)
    update_query = db.query(models.Order).filter(models.Order.id == new_order.id)
    update_query.update({'reference_id': customer_reference})
    db.commit()

    for item in order.items:
        new_order_item = models.OrderItem(order_id=new_order.id, product_id=item.id, quantity=item.quantity)
        db.add(new_order_item)
    db.commit()

    try:
        # Create a PaymentIntent with the order amount and currency
        intent = stripe.PaymentIntent.create(
            amount=int(total * 100),
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            },
            receipt_email=order.email,
            description=f"Thank you for your order at Bargain Liquor. Your order reference is #{customer_reference}",
        )
        return {
            'clientSecret': intent['client_secret'], 'orderId': new_order.id, 'total': total
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=str(e))

''' 
Check if order is valid before payment
An order (with order.id = order_id) is considered valid if 
1. The order is present in the database
2. order.status is not 'error'
3. If the order is a delivery order, customer's address must be in the delivery rang
'''
@router.put('/place/{order_id}')
def place_order(order_id: int, db: Session = Depends(get_db)):
    update_query = db.query(models.Order).filter(models.Order.id == order_id)
    old_order = update_query.first()
    if old_order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="session expired or order does not exist")
    if old_order.status == 'placed':
        # this should only happen when order details have passed check but payment didn't go through
        return
    if old_order.status == 'error':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, 
                            detail="An unexpected error occurred.")
    if old_order.order_type == 'delivery':
        if old_order.address_line_2:
            addr = old_order.address_line_1 + ' ' + old_order.address_line_2 + ', ' + old_order.city + ', ' + old_order.state + ' ' + old_order.zip_code
        else:
            addr = old_order.address_line_1 + ', ' + old_order.city + ', ' + old_order.state + ' ' + old_order.zip_code
        isin_range, error_message = check_addr_within_range(addr)
        if not isin_range:
            update_query.update({'status': 'error'})
            db.commit()
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=error_message)
    update_query.update({'status': 'placed'})
    db.commit()
    return {"msg": "Order is placed successfully"}

@router.put('/confirm/{order_id}')
def confirm_payment(order_id: int, db: Session = Depends(get_db)):
    update_query = db.query(models.Order).filter(models.Order.id == order_id)
    old_order = update_query.first()
    if old_order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="order does not exist")
    update_query.update({'status': 'confirmed'})
    db.commit()
    txt_message = f"An order (#{old_order.reference_id}) has been placed on online store. Customer Name - {old_order.first_name} {old_order.last_name}. Order Type - {old_order.order_type}."
    if old_order.order_type == 'delivery':
        if old_order.address_line_2:
            address = old_order.address_line_1 + ' ' + old_order.address_line_2 + ', ' + old_order.city + ', ' + old_order.state + ' ' + old_order.zip_code
        else:
            address = old_order.address_line_1 + ', ' + old_order.city + ', ' + old_order.state + ' ' + old_order.zip_code
        txt_message += 'Address - ' + address
    txt_message += f'\nLink - {settings.client_hostname}/order/{old_order.id}'
    send_txt_message(settings.order_confirm_contact, "@msg.fi.google.com", txt_message)
    return {"msg": "Success"}

@router.put('/error/{order_id}')
def payment_error(order_id: int, db: Session = Depends(get_db)):
    update_query = db.query(models.Order).filter(models.Order.id == order_id)
    old_order = update_query.first()
    if old_order == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="order does not exist")
    update_query.update({'status': 'error'})
    db.commit()
    return {'msg': f'Status of order #{order_id} has been updated to error'}

@router.put('/accept/{order_id}', response_model=schemas.OrderDetailResponse)
def accept_order(order_id: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.is_admin:
        update_query = db.query(models.Order).filter(models.Order.id == order_id)
        old_order = update_query.first()
        if old_order == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="order does not exist")
        update_query.update({'status': 'accepted'})
        db.commit()
        return update_query.first()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Permission denied.")
    
@router.put('/complete/{order_id}', response_model=schemas.OrderDetailResponse)
def complete_order(order_id: int, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.is_admin:
        update_query = db.query(models.Order).filter(models.Order.id == order_id)
        old_order = update_query.first()
        if old_order == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="order does not exist")
        update_query.update({'status': 'completed'})
        db.commit()
        # update inventory
        for item in old_order.items:
            product_id = item.product_id
            update_product = db.query(models.Product).filter(models.Product.id == product_id)
            product = update_product.first()
            update_product.update({'inventory': product.inventory - item.quantity})
            db.commit()
        return update_query.first()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Permission denied.")
    
@router.put('/cancel/{order_id}', response_model=schemas.OrderDetailResponse)
def cancel_order(order_id: int, reason: schemas.OrderCancel, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.is_admin:
        update_query = db.query(models.Order).filter(models.Order.id == order_id)
        old_order = update_query.first()
        if old_order == None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail="order does not exist")
        update_query.update({'status': 'canceled', 'cancel_reason': reason.reason})
        db.commit()
        return update_query.first()
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Permission denied.")

@router.get('/all', response_model=List[schemas.OrderResponse])
def get_all_orders(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and user.is_admin:
        all_orders = db.query(models.Order).all()
        return all_orders
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Permission denied.")
    
@router.get('/detail/{id}', response_model=schemas.OrderDetailResponse)
def get_order_detail(id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if order:
        return order
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                        detail="order does not exist")

'''
Delete all orders that satisfy the one of the following:
1. Order is created before 15 minutes ago and the order's status is either 'created' or 'error'
2. Order is created before 20 minutes ago and the order's status is 'placed'
'''
def clean_expired_orders(db: Session = Depends(get_db)):
    current_time = datetime.datetime.now()
    fifteen_min_ago = current_time - datetime.timedelta(minutes=15)
    twenty_min_ago = current_time - datetime.timedelta(minutes=20)
    clean_query = db.query(models.Order).filter(((models.Order.created_at < fifteen_min_ago) &
                                                ((models.Order.status == 'created') | (models.Order.status == 'error'))) |
                                                ((models.Order.created_at < twenty_min_ago) & (models.Order.status == 'placed')))
    clean_query.delete(synchronize_session=False)
    db.commit()

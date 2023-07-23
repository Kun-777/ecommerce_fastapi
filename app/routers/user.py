from fastapi import status, HTTPException, Depends, APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi_jwt_auth import AuthJWT
import datetime
from ..database import get_db
from .. import models, schemas
from ..utils import get_password_hash, verify_password, send_verification_email
from ..config import settings

router = APIRouter(prefix='/user')

templates = Jinja2Templates(directory='templates')

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # hash the password
    hashed_password = get_password_hash(user.password)
    user.password = hashed_password

    new_user = models.User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # email verification
    await send_verification_email(user.email)
    return {"msg":"Successfully registered"}

@router.put('/edit_profile')
def edit_profile(user_edit: schemas.UserProfileChange, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        update_query = db.query(models.User).filter(models.User.id == user.id)
        update_query.update(user_edit.dict(), synchronize_session=False)
        db.commit()
        return {"first_name": user_edit.first_name, "msg": "Profile has been successfully updated."}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

@router.put('/change_address')
def change_address(addr: schemas.Address, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        update_query = db.query(models.User).filter(models.User.id == user.id)
        update_query.update(addr.dict(), synchronize_session=False)
        db.commit()
        return {"msg": "Address has been successfully updated."}
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")

@router.put('/change_password')
def change_password(passwords: schemas.UserChangePassword, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user and verify_password(passwords.old_password, user.password):
        hashed_password = get_password_hash(passwords.new_password)
        update_query = db.query(models.User).filter(models.User.id == user.id)
        update_query.update({"password": hashed_password}, synchronize_session=False)
        db.commit()
        return {"msg": "Your password has been successfully updated."}
    elif user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="User not found")
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Old password you entered does not match the information we have on file")

@router.post('/login', response_model=schemas.UserLoginResponse)
def login(user_credentials: schemas.UserLogin, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials"
        )
    at_expires = datetime.timedelta(minutes=settings.access_token_expire_minutes)
    rt_expires = datetime.timedelta(days=settings.refresh_token_expire_days)
    access_token = Authorize.create_access_token(subject=user.id, expires_time=at_expires)
    refresh_token = Authorize.create_refresh_token(subject=user.id, expires_time=rt_expires)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)
    return {"access_token": access_token, "first_name": user.first_name, "is_admin": user.is_admin}

@router.post('/login_no_refresh', response_model=schemas.UserLoginResponse)
def login_no_refresh(user_credentials: schemas.UserLogin, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials")
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Credentials"
        )
    at_expires = datetime.timedelta(hours=2)
    access_token = Authorize.create_access_token(subject=user.id, expires_time=at_expires)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    return {"access_token": access_token, "first_name": user.first_name, "is_admin": user.is_admin}

@router.post('/refresh', response_model=schemas.UserLoginResponse)
def refresh(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    """
    The jwt_refresh_token_required() function insures a valid refresh
    token is present in the request before running any code below that function.
    we can use the get_jwt_subject() function to get the subject of the refresh
    token, and use the create_access_token() function again to make a new access token
    """
    Authorize.jwt_refresh_token_required()

    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        at_expires = datetime.timedelta(minutes=settings.access_token_expire_minutes)
        new_access_token = Authorize.create_access_token(subject=user_id, expires_time=at_expires)
        Authorize.set_access_cookies(new_access_token)
        return {"access_token": new_access_token, "first_name": user.first_name, "is_admin": user.is_admin}
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token or expired token")

@router.delete('/logout')
def logout(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

    Authorize.unset_jwt_cookies()
    return {"msg":"Successfully logout"}

@router.get('/profile', response_model=schemas.UserProfileResponse)
def profile(Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        return user
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token or expired token")

@router.post('/verify_email', response_class=HTMLResponse)
def verify_email(request: Request, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    Authorize.jwt_required()
    user_id = Authorize.get_jwt_subject()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        update_query = db.query(models.User).filter(models.User.id == user.id)
        update_query.update({"is_verified": True}, synchronize_session=False)
        db.commit()
        return templates.TemplateResponse("email_verification.html", {"request": request, "username": user.first_name})
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token or expired token")
    


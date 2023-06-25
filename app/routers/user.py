from fastapi import status, HTTPException, Depends, APIRouter, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from fastapi_jwt_auth import AuthJWT
from ..database import get_db
from .. import models, schemas
from ..utils import get_password_hash, verify_password, send_verification_email
from ..oauth2 import create_access_token, get_current_user

router = APIRouter()

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
    # automatically log the user in
    access_token = create_access_token(data = {"user_email": user.email})
    # email verification
    await send_verification_email([user.email], access_token)
    return {"access_token": access_token, "token_type": "bearer"}

# @router.post('/login', response_model=schemas.Token)
# def login(user_credentials: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
#     user = db.query(models.User).filter(models.User.email == user_credentials.username).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
#     if not verify_password(user_credentials.password, user.password):
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
#         )
#     # create a JWT token
#     access_token = create_access_token(data = {"user_email": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}

@router.post('/login', response_model=schemas.Token)
def login(user_credentials: schemas.UserLogin, Authorize: AuthJWT = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_credentials.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials")
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid Credentials"
        )
    access_token = Authorize.create_access_token(subject=user.email)
    refresh_token = Authorize.create_refresh_token(subject=user.email)

    # Set the JWT cookies in the response
    Authorize.set_access_cookies(access_token)
    Authorize.set_refresh_cookies(refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post('/refresh')
def refresh(Authorize: AuthJWT = Depends()):
    """
    The jwt_refresh_token_required() function insures a valid refresh
    token is present in the request before running any code below that function.
    we can use the get_jwt_subject() function to get the subject of the refresh
    token, and use the create_access_token() function again to make a new access token
    """
    Authorize.jwt_refresh_token_required()

    current_user = Authorize.get_jwt_subject()
    new_access_token = Authorize.create_access_token(subject=current_user)
    Authorize.set_access_cookies(new_access_token)
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.delete('/logout')
def logout(Authorize: AuthJWT = Depends()):
    Authorize.jwt_required()

    Authorize.unset_jwt_cookies()
    return {"msg":"Successfully logout"}

@router.get('/verify_email', response_class=HTMLResponse)
def verify_email(request: Request, token: str, db: Session = Depends(get_db)):
    user = get_current_user(token=token, db=db)
    if user:
        update_query = db.query(models.User).filter(models.User.email == user.email)
        update_query.update({"is_verified": True}, synchronize_session=False)
        db.commit()
        return templates.TemplateResponse("email_verification.html", {"request": request, "username": user.email})
    else:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token or expired token")
    


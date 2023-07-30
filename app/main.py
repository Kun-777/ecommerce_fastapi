from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from pydantic import BaseModel
from . import models
from .database import engine
from .routers import product, user, cart, order
from .config import settings
import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.include_router(product.router)
app.include_router(user.router)
app.include_router(cart.router)
app.include_router(order.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f'https://{settings.client_hostname}'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuthJWTSettings(BaseModel):
    authjwt_secret_key: str = settings.authjwt_secret_key
    # Configure application to store and get JWT from cookies
    authjwt_token_location: set = {"cookies"}
    # Only allow JWT cookies to be sent over https
    authjwt_cookie_secure: bool = True
    # Enable csrf double submit protection. default is True
    authjwt_cookie_csrf_protect: bool = True
    # Change to 'lax' in production to make your website more secure from CSRF Attacks, default is None
    authjwt_cookie_samesite: str = 'none'

@AuthJWT.load_config
def get_config():
    return AuthJWTSettings()

@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=403,
        content={"detail": exc.message}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logging.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
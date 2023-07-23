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
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=["*"],
)

class AuthJWTSettings(BaseModel):
    authjwt_secret_key: str = settings.secret_key
    # Configure application to store and get JWT from cookies
    authjwt_token_location: set = {"cookies"}
    # Disable CSRF Protection for this example. default is True
    authjwt_cookie_csrf_protect: bool = False

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




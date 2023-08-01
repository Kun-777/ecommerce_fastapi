from pydantic import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: str
    database_name: str
    database_username: str
    database_password: str
    authjwt_secret_key: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    tax_rate: float
    delivery_fee: float
    smtp_email: str
    smtp_pwd: str
    order_confirm_contact: str
    store_addr: str
    google_map_api_key: str
    delivery_range: int
    stripe_api_key: str
    client_hostname: str
    image_path: str

    class Config:
        env_file = ".env"

settings = Settings()
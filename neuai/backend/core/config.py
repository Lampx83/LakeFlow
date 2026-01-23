import os

SECRET_KEY = os.getenv("SECRET_KEY", "neuai-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

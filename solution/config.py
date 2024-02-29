import os

DATABASE_URL = os.getenv("POSTGRES_CONN").replace("postgres://", "postgresql://")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change_me_pls")

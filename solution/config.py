import os

DATABASE_URL = os.getenv("POSTGRES_CONN").replace("postgres://", "postgresql://")

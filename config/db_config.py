# config/db_config.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Carrega variáveis de ambiente do .env
load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DATABASE_URL = (
    f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# Cria engine SQLAlchemy
engine = create_engine(DATABASE_URL)

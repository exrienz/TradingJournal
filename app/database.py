from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

# Default values if environment variables are not set
DB_USER = os.getenv('MYSQL_USER', 'trading_user')
DB_PASSWORD = os.getenv('MYSQL_PASSWORD', 'trading_password')
DB_HOST = os.getenv('DB_HOST', 'db')
DB_NAME = os.getenv('MYSQL_DATABASE', 'trading_journal')

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}?charset=utf8mb4"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    connect_args={"connect_timeout": 10}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from . import models
    # Create tables if they do not exist
    models.Base.metadata.create_all(bind=engine)

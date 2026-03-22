import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 确保数据目录存在
DATA_DIR = os.getenv("DATA_DIR", "./data")
os.makedirs(DATA_DIR, exist_ok=True)

# SQLite 数据库路径
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/copyhub.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite 需要这个参数
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
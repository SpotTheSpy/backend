from datetime import datetime

from sqlalchemy import Column, UUID, func, String, DateTime, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(True), primary_key=True, server_default=func.gen_random_uuid())
    telegram_id = Column(BigInteger(), unique=True, nullable=False, index=True)
    first_name = Column(String(64), nullable=False)
    username = Column(String(32), unique=True, nullable=True, default=None)
    locale = Column(String(8), nullable=True, default=None)
    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(), nullable=True, onupdate=datetime.now)

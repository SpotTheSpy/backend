from datetime import datetime

from sqlalchemy import Column, UUID, func, String, DateTime, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    """
    Database user object.

    Attributes:
        id: UUID.
        telegram_id: User's telegram ID.
        first_name: First name from telegram.
        username: Username from telegram.
        locale: User's locale. Used to localize telegram responses.
        created_at: User's creation date.
        updated_at: User's last update date.
    """

    __tablename__ = "users"

    id = Column(UUID(True), primary_key=True, server_default=func.gen_random_uuid())
    """
    UUID.
    """

    telegram_id = Column(BigInteger(), unique=True, nullable=False, index=True)
    """
    User's telegram ID.
    """

    first_name = Column(String(64), nullable=False)
    """
    First name from telegram.
    """

    username = Column(String(32), unique=True, nullable=True, default=None)
    """
    Username from telegram.
    """

    locale = Column(String(8), nullable=True, default=None)
    """
    User's locale. Used to localize telegram responses.
    """

    created_at = Column(DateTime(), nullable=False, default=datetime.now)
    """
    User's creation date.
    """

    updated_at = Column(DateTime(), nullable=True, onupdate=datetime.now)
    """
    User's last update date.
    """

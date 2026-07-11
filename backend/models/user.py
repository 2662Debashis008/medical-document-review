from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, nullable=False)

    email = Column(String, unique=True, nullable=False)

    reviews = relationship("Review", back_populates="reviewer")
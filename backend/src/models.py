
from enum import Enum as PyEnum

from sqlalchemy import Column, Enum, Date, ForeignKey, Integer, String, UniqueConstraint
from src.database import Base


class ReadingStatusEnum(PyEnum):
    want_to_read = "want_to_read"
    reading = "reading"
    finished = "finished"


class BaseModel(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True)


class Book(BaseModel):
    __tablename__ = "book"

    title = Column(String, index=True)
    isbn = Column(String, unique=True)
    publisher_id = Column(Integer, ForeignKey("publisher.id"))


class Author(BaseModel):
    __tablename__ = "author"

    name = Column(String)


class BookAuthor(BaseModel):
    __tablename__ = "book_author"

    book_id = Column(Integer, ForeignKey("book.id"))
    author_id = Column(Integer, ForeignKey("author.id"))


class City(BaseModel):
    __tablename__ = "city"

    name = Column(String)
    postcode = Column(String)


class Publisher(BaseModel):
    __tablename__ = "publisher"

    company_name = Column(String)
    city_id = Column(Integer, ForeignKey("city.id"))


class User(BaseModel):
    __tablename__ = "user"

    name = Column(String)
    email = Column(String, unique=True)


class UserTracking(BaseModel):
    __tablename__ = "user_tracking"

    user_id = Column(Integer, ForeignKey("user.id"))
    book_id = Column(Integer, ForeignKey("book.id"))
    reading_status = Column(Enum(ReadingStatusEnum))
    started_at = Column(Date, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "book_id", name="uq_user_book"),
    )

from datetime import date
from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import ReadingStatusEnum


def create_user_tracking(book_id: int, db: Session, user_id: int = 1):
    db.execute(text("insert into user_tracking (user_id, book_id, reading_status, started_at) values (:user_id, :book_id, :reading_status, :started_at)"), {"user_id": user_id, "book_id": book_id, "reading_status": ReadingStatusEnum.want_to_read.value, "started_at": date.today()})


def get_or_create_publisher(db: Session, publisher_name: str):
    publisher_query = db.execute(text("SELECT id from publisher WHERE company_name = :company_name"), {"company_name": publisher_name})
    publisher_id = publisher_query.scalar()
    if publisher_id is None:
        # defaulted city_id
        result = db.execute(text("INSERT INTO publisher (company_name, city_id) VALUES (:company_name, 1) RETURNING id"), {"company_name": publisher_name})
        publisher_id = result.scalar()
    
    return publisher_id


def get_or_create_author(db: Session, author_name: str):
    author_query = db.execute(text("SELECT id from author where name=:name"), {"name": author_name})
    author_id = author_query.scalar()
    if author_id is None:
        result = db.execute(text("INSERT INTO author (name) VALUES (:name) RETURNING id"), {"name": author_name})
        author_id = result.scalar()
    
    return author_id

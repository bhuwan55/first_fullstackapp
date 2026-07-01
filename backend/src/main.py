from typing import List

from fastapi import FastAPI, Depends, APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from .models import ReadingStatusEnum

from .utils import create_user_tracking, get_or_create_author, get_or_create_publisher

from .database import get_db
from pydantic import BaseModel as PydanticBaseModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

api_router = APIRouter()

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@api_router.get("/")
async def root():
    return {"message": "Hello World"}


class BookRead(PydanticBaseModel):
    id: int
    title: str
    publisher_id: int
    isbn: str
    publisher_name: str | None
    author_name: str | None
    started_at: str | None
    reading_status: str | None

@api_router.get("/books", response_model=List[BookRead])
async def get_books(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT b.id, b.title, b.publisher_id, b.isbn, " \
    "p.company_name AS publisher_name, a.name AS author_name, " \
    "ut.started_at, ut.reading_status FROM book b " \
    "LEFT JOIN publisher p ON b.publisher_id = p.id " \
    "LEFT JOIN book_author ba ON ba.book_id = b.id " \
    "LEFT JOIN author a ON ba.author_id = a.id " \
    "LEFT JOIN user_tracking ut ON ut.book_id = b.id AND ut.user_id = 1")
    )
    books = result.fetchall()

    return books


class BookCreate(PydanticBaseModel):
    title: str
    isbn: str
    publisher_name: str | None
    author_name: str | None


@api_router.post("/books", response_model=dict)
async def create_books(book_data: BookCreate, db: Session = Depends(get_db)):
    try:
        publisher_id = get_or_create_publisher(db, book_data.publisher_name)

        author_id = get_or_create_author(db, book_data.author_name)
        
        book_result = db.execute(
            text("INSERT INTO book (title, isbn, publisher_id) VALUES (:title, :isbn, :publisher_id) RETURNING id"),
            {"title": book_data.title, "isbn": book_data.isbn, "publisher_id": publisher_id},
        )
        book_id = book_result.scalar()

        db.execute(text("INSERT INTO book_author (book_id, author_id) VALUES (:book_id, :author_id)"), {"book_id": book_id, "author_id": author_id})

        create_user_tracking(book_id=book_id, db=db)

        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


@api_router.patch("/books/{book_id}", response_model=dict)
async def update_reading_status(book_id: int, reading_status: str, db: Session = Depends(get_db)):
    delete_stmt = text("DELETE FROM book WHERE id = :book_id")

    db.execute(delete_stmt, {"book_id": 1})
    db.commit()
    current_reading_status = db.scalar(text(" SELECT reading_status FROM user_tracking WHERE book_id = :book_id AND user_id = 1"), {"book_id": book_id})
    allowed_statuses_transitions = {
        ReadingStatusEnum.want_to_read.value: [ReadingStatusEnum.reading.value, ReadingStatusEnum.finished.value],
        ReadingStatusEnum.reading.value: [ReadingStatusEnum.finished.value],
    }
    print(current_reading_status, allowed_statuses_transitions.get(current_reading_status, []), reading_status)
    if not current_reading_status:
        return {"success": False, "error": "No current reading status found for the book."}
    
    if not allowed_statuses_transitions.get(current_reading_status, []) or reading_status not in allowed_statuses_transitions[current_reading_status]:
        return {"success": False, "error": f"Invalid status transition from {current_reading_status} to {reading_status}"}

    try:
        stmt = text("UPDATE user_tracking SET reading_status = :reading_status WHERE book_id = :book_id AND user_id = 1")
        db.execute(stmt, {"reading_status": reading_status, "book_id": book_id})
        db.commit()
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    return {"success": True}

app.include_router(api_router, prefix='/api')

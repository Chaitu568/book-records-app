from sqlalchemy.orm import Session
from app import models, schemas
from app.utils import hash_password
from app.events import event_manager

# User-related operations
def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hash_password(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Book-related operations
def get_books(db: Session, skip: int, limit: int):
    return db.query(models.Book).offset(skip).limit(limit).all()

def get_book(db: Session, book_id: int):
    return db.query(models.Book).filter(models.Book.id == book_id).first()

async def create_book(db: Session, book: schemas.BookCreate):
    db_book = models.Book(**book.dict())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    
    # Emit book created event
    await event_manager.emit("book_created", {
        "id": db_book.id,
        "title": db_book.title,
        "author": db_book.author,
        "genre": db_book.genre
    })
    return db_book

async def update_book(db: Session, book_id: int, book: schemas.BookCreate):
    db_book = get_book(db, book_id)
    if not db_book:
        return None
        
    for key, value in book.dict().items():
        if value is not None:
            setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    
    # Emit book updated event
    await event_manager.emit("book_updated", {
        "id": db_book.id,
        "title": db_book.title,
        "author": db_book.author,
        "genre": db_book.genre
    })
    return db_book

async def delete_book(db: Session, book_id: int):
    db_book = get_book(db, book_id)
    if db_book:
        # Store book info before deletion
        book_info = {
            "id": db_book.id,
            "title": db_book.title
        }
        db.delete(db_book)
        db.commit()
        
        # Emit book deleted event
        await event_manager.emit("book_deleted", book_info)
        return True
    return False
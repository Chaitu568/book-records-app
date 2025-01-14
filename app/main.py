from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
import asyncio
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware

from app import models, schemas, crud, auth, db, utils

models.Base.metadata.create_all(bind=db.engine)

app = FastAPI(
    title="Book Records API",
    description="CRUD operations for managing books, with JWT authentication and real-time updates.",
    version="1.0.0"
)


# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Book Records App"}


# Dependency to get DB session
def get_db():
    db_session = db.SessionLocal()  # Use a different name for the local variable
    try:
        yield db_session
    finally:
        db_session.close()

@app.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user(db, username=form_data.username)
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/books/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    auth.verify_token(token)
    return crud.create_book(db=db, book=book)

@app.get("/books/", response_model=list[schemas.Book])
def read_books(skip: int = 0, limit: int = 10, db: Session = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    auth.verify_token(token)
    return crud.get_books(db=db, skip=skip, limit=limit)

@app.get("/books/{book_id}", response_model=schemas.Book)
def read_book(book_id: int, db: Session = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    auth.verify_token(token)
    book = crud.get_book(db=db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookCreate, db: Session = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    auth.verify_token(token)
    updated_book = crud.update_book(db=db, book_id=book_id, book=book)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), token: str = Depends(auth.oauth2_scheme)):
    auth.verify_token(token)
    book = crud.get_book(db=db, book_id=book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    crud.delete_book(db=db, book_id=book_id)
    return {"message": "Book deleted successfully"}

@app.get("/stream", response_class=StreamingResponse)
async def stream_updates():
    async def event_stream():
        while True:
            yield f"data: {datetime.utcnow()}\n\n"
            await asyncio.sleep(1)
    try:
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/users/", response_model=schemas.User)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)
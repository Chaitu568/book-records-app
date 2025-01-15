from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse
import asyncio
from datetime import datetime
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.responses import HTMLResponse 

from app import models, schemas, crud, auth, db, utils
from app.events import event_manager

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

@app.post("/users/", response_model=schemas.User)
def create_new_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)



@app.post("/books/", response_model=schemas.Book)
async def create_book(
    book: schemas.BookCreate, 
    db: Session = Depends(get_db), 
    token: str = Depends(auth.oauth2_scheme)
):
    auth.verify_token(token)
    return await crud.create_book(db=db, book=book)

@app.put("/books/{book_id}", response_model=schemas.Book)
async def update_book(
    book_id: int, 
    book: schemas.BookCreate, 
    db: Session = Depends(get_db), 
    token: str = Depends(auth.oauth2_scheme)
):
    auth.verify_token(token)
    updated_book = await crud.update_book(db=db, book_id=book_id, book=book)
    if not updated_book:
        raise HTTPException(status_code=404, detail="Book not found")
    return updated_book

@app.delete("/books/{book_id}")
async def delete_book(
    book_id: int, 
    db: Session = Depends(get_db), 
    token: str = Depends(auth.oauth2_scheme)
):
    auth.verify_token(token)
    success = await crud.delete_book(db=db, book_id=book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted successfully"}


@app.get("/stream/html", response_class=HTMLResponse)
async def stream_page():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Book Updates Stream</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 40px; 
                    background-color: #f5f5f5;
                }
                h1 {
                    color: #333;
                    margin-bottom: 20px;
                }
                #events { 
                    margin-top: 20px;
                    padding: 20px;
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    min-height: 200px;
                    max-height: 600px;
                    overflow-y: auto;
                    background-color: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .event {
                    margin: 10px 0;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #ccc;
                    animation: fadeIn 0.5s ease-in;
                }
                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(-10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
                .book_created {
                    background-color: #e3f2fd;
                    border-left-color: #2196F3;
                }
                .book_updated {
                    background-color: #f1f8e9;
                    border-left-color: #4CAF50;
                }
                .book_deleted {
                    background-color: #ffebee;
                    border-left-color: #f44336;
                }
                .timestamp {
                    color: #666;
                    font-size: 0.9em;
                    margin-bottom: 5px;
                }
                .status {
                    margin-top: 10px;
                    padding: 10px;
                    border-radius: 4px;
                    background-color: #e8eaf6;
                    text-align: center;
                }
                .error {
                    background-color: #ffebee;
                    color: #c62828;
                }
            </style>
        </head>
        <body>
            <h1>📚 Real-time Book Updates</h1>
            <div class="status" id="status">Connecting to server...</div>
            <div id="events"></div>

            <script>
                const eventsDiv = document.getElementById('events');
                const statusDiv = document.getElementById('status');
                let eventSource;

                function connect() {
                    statusDiv.textContent = 'Connecting to server...';
                    statusDiv.className = 'status';
                    
                    eventSource = new EventSource('/stream/data');
                    
                    eventSource.onopen = function() {
                        statusDiv.textContent = '🟢 Connected - Listening for book updates...';
                        statusDiv.style.backgroundColor = '#e8f5e9';
                    };

                    eventSource.onmessage = function(event) {
                        try {
                            const data = JSON.parse(event.data);
                            console.log('Received event:', data);  // Debug log
                            
                            const newEvent = document.createElement('div');
                            newEvent.className = `event ${data.type || ''}`;
                            
                            const timestamp = document.createElement('div');
                            timestamp.className = 'timestamp';
                            timestamp.textContent = new Date(data.timestamp).toLocaleString();
                            
                            const content = document.createElement('div');
                            let message = '';
                            
                            if (data.type === 'book_created') {
                                message = `📗 New book added: "${data.data.title}" by ${data.data.author}`;
                            } else if (data.type === 'book_updated') {
                                message = `📘 Book updated: "${data.data.title}" by ${data.data.author}`;
                            } else if (data.type === 'book_deleted') {
                                message = `📕 Book deleted: "${data.data.title}" (ID: ${data.data.id})`;
                            } else {
                                message = JSON.stringify(data.data || data.message || data);
                            }
                            
                            content.textContent = message;
                            
                            newEvent.appendChild(timestamp);
                            newEvent.appendChild(content);
                            eventsDiv.insertBefore(newEvent, eventsDiv.firstChild);
                            
                            // Keep only last 50 events
                            if (eventsDiv.children.length > 50) {
                                eventsDiv.removeChild(eventsDiv.lastChild);
                            }
                        } catch (error) {
                            console.error('Error processing event:', error);
                        }
                    };
                    
                    eventSource.onerror = function(error) {
                        console.error('EventSource failed:', error);
                        statusDiv.textContent = '🔴 Connection lost. Reconnecting...';
                        statusDiv.className = 'status error';
                        eventSource.close();
                        setTimeout(connect, 5000);  // Try to reconnect after 5 seconds
                    };
                }

                // Initial connection
                connect();

                // Cleanup on page unload
                window.addEventListener('beforeunload', () => {
                    if (eventSource) {
                        eventSource.close();
                    }
                });
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content)
                    
           
@app.get("/stream/data", response_class=StreamingResponse)
async def stream_data():
    async def event_stream():
        try:
            listener_id, queue = await event_manager.register()
            while True:
                try:
                    event = await queue.get()
                    if event:
                        yield f"data: {json.dumps(event)}\n\n"
                except Exception as e:
                    print(f"Error in stream: {e}")
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except asyncio.CancelledError:
            event_manager.deregister(listener_id)
        finally:
            event_manager.deregister(listener_id)
            
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*"
        }
    )
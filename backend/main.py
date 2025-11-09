from typing import Union, Annotated
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, get_db
from .models import Event, User, Base, EventType
from . import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/")
def read_root():
    return {"Hello": "World"}

# Get the list of users from the database
@app.get("/users")
async def get_users(db: db_dependency):
    return db.query(User).all()

# Get info for a specific user
@app.get("/users/{user_id}")
async def get_user(db: db_dependency, user_id: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user is not None:
        return user
    raise HTTPException(status_code=200, detail="User not found")

@app.post("/users", status_code=201)
async def create_user(db: db_dependency, user_request: schemas.UserRequest):
    new_user = User(**user_request.model_dump())
    db.add(new_user)
    db.commit()

@app.get("/migraines")
async def get_migraines(db: db_dependency, user_id: str):
    migraines = db.query(Event).filter(Event.user_id == user_id, Event.event_type == EventType.migraine).all()
    if migraines is not None:
        return migraines
    return []

@app.post("/event")
async def create_event(db: db_dependency, user_id: str, event_request: schemas.EventRequest):
    new_event = Event(user_id=user_id, **event_request.model_dump())
    db.add(new_event)
    db.commit()

@app.get("/triggers")
async def get_triggers(db: db_dependency, user_id: str):
    other_events = db.query(Event).filter(Event.user_id == user_id, Event.event_type != EventType.migraine).all()
    if other_events is not None:
        return other_events
    return []
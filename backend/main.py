import random
import datetime

from typing import Union, Annotated
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, get_db
from .models import Event, User, Base, EventType, Severity, Unit
from . import schemas

Base.metadata.create_all(bind=engine)

VARS = {
    'migraineSystem': 'LOINC',
    'migraineCode': 'LA15141-7',
    'sleepSystem': 'ICD-10',
    'sleepCode': 'Y93.84',
    'stressSystem': 'ICD-10',
    'stressCode': 'Z73.3',
    'mealSystem': 'ICD-10',
    'mealCode': 'Y93.G1'
}

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

@app.get("/api")
def read_root():
    return {"Hello": "World"}

# Get the list of users from the database
@app.get("/api/users")
async def get_users(db: db_dependency):
    return db.query(User).all()

# Get info for a specific user
@app.get("/api/users/{user_id}")
async def get_user(db: db_dependency, user_id: str):
    user = db.query(User).filter(User.id == user_id).first()
    if user is not None:
        return user
    raise HTTPException(status_code=200, detail="User not found")

@app.post("/api/users", status_code=201)
async def create_user(db: db_dependency, user_request: schemas.UserRequest):
    new_user = User(**user_request.model_dump())
    db.add(new_user)
    db.commit()

@app.get("/api/migraines")
async def get_migraines(db: db_dependency, user_id: str):
    migraines = db.query(Event).filter(Event.user_id == user_id, Event.event_type == EventType.migraine).all()
    if migraines is not None:
        return migraines
    return []

@app.post("/api/event")
async def create_event(db: db_dependency, user_id: str, event_request: schemas.EventRequest):
    new_event = Event(user_id=user_id, **event_request.model_dump())
    db.add(new_event)
    db.commit()

@app.get("/api/triggers")
async def get_triggers(db: db_dependency, user_id: str):
    other_events = db.query(Event).filter(Event.user_id == user_id, Event.event_type != EventType.migraine).all()
    if other_events is not None:
        return other_events
    return []

def get_random_date_between(start_date: datetime.date, end_date: datetime.date):
    days_between = (end_date - start_date).days
    rand_days = random.randrange(days_between)
    return start_date + datetime.timedelta(days=rand_days)

@app.post("/api/populate", status_code=200)
async def populate_data(db: db_dependency):
    """
    Populates the database with a fixed set of data.
    4 Users,
    For each user:
    - 3 Migraine events
    - Random (1-4) Sleep events
    - Random (2-3) Stress events
    """
    names = ['Jessica', 'Albert', 'John', 'Susan']
    # Create a user for each name and then populate a map.
    users = [User(name=n) for n in names]
    db.add_all(users)
    db.flush()
    user_map = {u.name:u.id for u in users}
    random.seed(0)
    start_date = datetime.date(2025, 9, 30)
    end_date =  datetime.date(2025, 11, 3)
    for id in user_map.values():
        num_migraine_events = 3
        num_sleep_events = random.randint(1, 4)
        num_stress_events = random.randint(2, 3)
        # create migraine events
        for _ in range(num_migraine_events):
            m = Event(
                user_id=id,
                system=VARS['migraineSystem'],
                code=VARS['migraineCode'],
                event_type=EventType.migraine,
                severity=random.choice(list(Severity)),
                numerical_value=random.randint(5, 30),
                numerical_unit=Unit.minutes,
                description='Had a migraine',
                creation_timestamp=get_random_date_between(start_date, end_date)
                )
            db.add(m)
        for _ in range(num_sleep_events):
            s = Event(
                user_id=id,
                system=VARS['sleepSystem'],
                code=VARS['sleepCode'],
                event_type=EventType.sleep,
                numerical_value=random.randint(5, 13),
                numerical_unit=Unit.hours,
                description='Got some sleep',
                creation_timestamp=get_random_date_between(start_date, end_date)
                )
            db.add(s)
        for _ in range(num_stress_events):
            s = Event(user_id=id,
                system=VARS['stressSystem'],
                code=VARS['stressCode'],
                event_type=EventType.stress,
                severity=random.choice(list(Severity)),
                description='Had stress today',
                creation_timestamp=get_random_date_between(start_date, end_date))
            db.add(s)
    db.commit()
    return {'status': "OK"}

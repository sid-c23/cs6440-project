import random
import os
import datetime

from typing import Union, Annotated, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, get_db
from .models import Event, User, Base, EventType, Severity, Unit
from . import schemas

from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.observation import Observation
from fhirclient.models.encounter import Encounter
from fhirclient.models.fhirreference import FHIRReference

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


"""
Next thing: use Fhir Client somehow

A. Create Fhir compatible objects using the data we have (export function)
    1. Read from database (just patients for now?)
B. Use the objects and send to the HAPI demo fhir server
    1. https://hapi.fhir.org/baseR4 
"""

def convert_user_to_fhir(user: User):
    patient = Patient({
        'active': True,
        'identifier': [{
            'use': 'usual',
            'value': str(user.id)
        }, {
            'use': 'temp',
            'value': 'mitigate-app'
        }],
        'name': [{
            'use': 'official',
            'text': user.name
        }]
    })
    return patient

def convert_event_to_fhir(event: Event):
    return Observation({
        'status': 'registered',
        'code': {
            'coding': [{
                'system': event.system,
                'code': event.code
            }],
            'text': event.event_type
        },
        'identifier': [
            {
                'use': 'usual',
                'value': str(event.id)
            },
            {
                'use': 'temp',
                'value': 'mitigate-app'
            }
        ],
        'valueCodeableConcept': {
            'coding': [
                {
                    'system': 'severity',
                    'code': str(event.severity)
                },
                {
                    'system': 'value',
                    'code': str(event.numerical_value)
                },
                {
                    'system': 'unit',
                    'code': str(event.numerical_unit)
                }
            ]
        },
        'note': [{
            # 'time': FHIRDateTime(event.creation_timestamp.isoformat()),
            'text': event.description
        }]
    })


@app.get("/api/get_patient_fhir/{user_id}", status_code=200)
async def get_patient_fhir(user_id: str):
    settings = {
        'app_id': 'mitigate_app',
        'api_base': 'https://hapi.fhir.org/baseR4'
    }
    smart = client.FHIRClient(settings=settings)
    search = Patient.where(struct={'identifier': user_id})
    res = [r.as_json() for r in search.perform_iter(smart.server)]
    return res
        
    # user = db.query(User).filter(User.id == user_id).first()
    # patient = convert_user_to_patient(db, user)
    # return {
    #     'user': user,
    #     'patient': patient.as_json()
    # }

# @app.post("/api/export_user_to_fhir/{user_id}", status_code=200)
# async def export_user_to_fhir(db: db_dependency, user_id: str):
#     user = db.query(User).filter(User.id == user_id).first()
#     patient = convert_user_to_fhir(user)
#     settings = {
#         'app_id': 'mitigate_app',
#         'api_base': 'https://hapi.fhir.org/baseR4'
#     }
#     smart = client.FHIRClient(settings=settings)
#     created = patient.create(smart.server)
#     return created

@app.get("/api/get_patient_info_from_fhir/{user_id}", status_code=200)
async def get_patient_info_from_fhir(user_id: str):
    settings = {
        'app_id': 'mitigate_app',
        'api_base': 'https://hapi.fhir.org/baseR4'
    }
    smart = client.FHIRClient(settings=settings)
    patients = Patient.where(struct={'identifier': user_id}).perform_resources(smart.server)
    if not patients:
        return {
            "ok": False,
            "error": f"No Patient found for identifier '{user_id}' on HAPI R4."
        }

    patient = patients[0]
    patient_json = patient.as_json()

    # 2) Fetch Observations linked to the Patient via subject reference
    #    This is the canonical way to get observations for a patient:
    #    GET [base]/Observation?subject=Patient/{patient_id}
    #    (Reference-type search param per FHIR search.) [2](https://smilecdr.com/docs/fhir_standard/fhir_search_references.html)
    obs_search = Observation.where(struct={"subject": f"Patient/{patient.id}"})
    observations = [obs.as_json() for obs in obs_search.perform_iter(smart.server)]

    return {
        "ok": True,
        "patient": patient_json,
        "observations": observations,
        "counts": {
            "patients": len(patients),
            "observations": len(observations)
        }
    }



@app.post("/api/export_patient_data_to_fhir/{user_id}", status_code=200)
async def export_patient_data_to_fhir(db: db_dependency, user_id: str):
    """
    Exports all of a user's data (patient data and all observation data) to the demo HAPI FHIR server.
    First, the Patient is created on the FHIR server.
    Second, the Observation data is created on the FHIR server.
    """
    settings = {
        'app_id': 'mitigate_app',
        'api_base': 'https://hapi.fhir.org/baseR4'
    }
    # -- Pull local data
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"ok": False, "error": f"User {user_id} not found"}

    events: List[Event] = db.query(Event).filter(Event.user_id == user_id).all()

    # -- Build FHIRClient
    smart = client.FHIRClient(settings=settings)

    # -- Create or reuse Patient
    patient_resource: Patient = convert_user_to_fhir(user)

    existing_patients = Patient.where(struct={'identifier': user_id}).perform_resources(smart.server)

    if existing_patients:
            patient = existing_patients[0].as_json()
            patient_id = patient['id']
            reused = True
    else:
        patient = patient_resource.create(smart.server)    # POST /Patient
        patient_id = patient['id']
        reused = False

    # -- Create Observations
    created_obs_ids: List[str] = []
    errors: List[Dict[str, Any]] = []

    for ev in events:
        try:
            obs: Observation = convert_event_to_fhir(ev)
            # Link Observation to Patient
            obs.subject = FHIRReference({'reference': f'Patient/{patient_id}'})
            created_obs = obs.create(smart.server)          # POST /Observation
            created_obs_ids.append(created_obs)
        except Exception as e:
            errors.append({
                "event_id": str(ev.id),
                "error": str(e)
            })

    return {
        "ok": True,
        "patient": {
            "id": patient_id,
            "reused": reused,
            "identifiers": [iden for iden in (patient['identifier'] or [])]
        },
        "observations": {
            "created_count": len(created_obs_ids),
            "ids": created_obs_ids
        },
        "errors": errors
    }

@app.get("/api/populate", status_code=200)
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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if ".." in full_path:
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(os.path.join(DIST_DIR, "index.html"))

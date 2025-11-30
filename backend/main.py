import random
import os

from typing import Union, Annotated, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .database import engine, get_db
from .models import Event, User, Base, EventType, Severity, Unit
from . import schemas

from sqlalchemy import func, cast, String, Float, and_, case
from fastapi import Query, Depends
from datetime import datetime, timedelta, date, time

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

def get_random_date_between(start_date: date, end_date: date):
    days_between = (end_date - start_date).days
    rand_days = random.randrange(days_between)
    return start_date + timedelta(days=rand_days)


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
                },
                {
                    'system': 'eventTimestamp',
                    'code': str(event.event_timestamp)
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


@app.get("/api/migraines/weekly")
async def get_migraines_weekly(
    db: db_dependency,
    user_id: str,
    use_localtime: bool = Query(False, description="Apply SQLite 'localtime' modifier before week calc")
):
    """
    Returns per-week migraine metrics for the given user:
      - week_start_monday: YYYY-MM-DD (Monday of that week)
      - event_count: number of migraine events in that week
      - avg_severity: average severity for that week's migraine events
    """

    # Normalize ISO-8601 timestamp: replace 'T' with ' ' and ensure text form
    ts_text = cast(Event.event_timestamp, String)
    ts_norm = func.replace(ts_text, 'T', ' ')

    # Build the week-start (Monday) expression using SQLite date() modifiers
    # Order matters: if use_localtime is True, apply 'localtime' *before* 'weekday 1' and '-7 days'
    if use_localtime:
        week_start = func.date(ts_norm, 'localtime', 'weekday 1', '-7 days')
    else:
        week_start = func.date(ts_norm, 'weekday 1', '-7 days')

    query = (
        db.query(
            week_start.label('week_start_monday'),
            func.count(Event.id).label('event_count'),
            func.avg(cast(Event.severity, Float)).label('avg_severity')
        )
        .filter(
            Event.user_id == user_id,
            Event.event_type == EventType.migraine
        )
        .group_by(week_start)
        .order_by(week_start)
    )

    rows = query.all()

    # Convert SQLAlchemy rows to plain JSON-friendly dicts
    return [
        {
            "week_start_monday": r.week_start_monday,
            "event_count": int(r.event_count),
            "avg_severity": float(r.avg_severity) if r.avg_severity is not None else None
        }
        for r in rows
    ]


@app.get("/api/weekly/rolling")
async def get_weekly_rolling(
    db: db_dependency,
    user_id: str,
    window_size: int = Query(4, ge=1, le=52, description="Rolling window size in weeks."),
    use_localtime: bool = Query(False, description="Apply SQLite 'localtime' before week bucketing."),
    start_date: str | None = Query(None, description="Optional YYYY-MM-DD lower bound (aligned to Monday)."),
    end_date: str | None = Query(None, description="Optional YYYY-MM-DD upper bound (aligned to Monday)."),
):
    """
    Returns a continuous weekly time series with:
      - week_start_monday: YYYY-MM-DD (Monday of the week)
      - migraine_events: count per week
      - migraine_avg_severity: average severity per week (NULL if none)
      - sleep_hours: sum per week (minutes -> hours)
      - stress_hours: sum per week (minutes -> hours)
      - meals_count: total meals per week (unit 'number')
      - *_prev: previous week's value (lag-1)
      - pct_*_change: percent change vs previous week (NULL when prev is NULL or 0)
      - ma_*: moving average over `window_size` weeks (including current week)
    """

    # --- Quick empty check using ORM (robust for GUID/BLOB user_id) ---
    total_events = (
        db.query(func.count(Event.id))
          .filter(Event.user_id == user_id)
          .scalar()
    )
    if not total_events:
        return []

    # --- Week bucket (Option B) ---
    ts_text = cast(Event.event_timestamp, String)
    ts_norm = func.replace(ts_text, 'T', ' ')
    if use_localtime:
        week_start = func.date(ts_norm, 'localtime', 'weekday 1', '-7 days')
    else:
        week_start = func.date(ts_norm, 'weekday 1', '-7 days')

    # --- Unit normalization into a single numeric 'value_std' ---
    # ✅ SQLAlchemy 2.0: pass whens as positional tuples
    value_std = case(
        (
            and_(Event.event_type == EventType.sleep,  Event.numerical_unit == Unit.minutes),
            cast(Event.numerical_value, Float) / 60.0
        ),
        (
            and_(Event.event_type == EventType.sleep,  Event.numerical_unit == Unit.hours),
            cast(Event.numerical_value, Float)
        ),
        (
            and_(Event.event_type == EventType.stress, Event.numerical_unit == Unit.minutes),
            cast(Event.numerical_value, Float) / 60.0
        ),
        (
            and_(Event.event_type == EventType.stress, Event.numerical_unit == Unit.hours),
            cast(Event.numerical_value, Float)
        ),
        (
            and_(Event.event_type == EventType.meals,  Event.numerical_unit == Unit.number),
            cast(Event.numerical_value, Float)
        ),
        else_=None
    )

    # --- Base rows for this user (ORM ensures GUID binding is correct) ---
    base_q = (
        db.query(
            week_start.label('week_start_monday'),
            Event.event_type.label('event_type'),
            Event.severity.label('severity'),
            value_std.label('value_std')
        )
        .filter(
            Event.user_id == user_id,
            Event.event_timestamp.isnot(None)  # avoid NULL buckets
        )
    ).subquery()

    # --- Weekly aggregation (sparse) ---
    weekly_q = (
        db.query(
            base_q.c.week_start_monday,

            # counts: sum of 1s for migraine rows
            func.sum(
                case(
                    (base_q.c.event_type == EventType.migraine, 1),
                    else_=0
                )
            ).label('migraine_events'),

            # avg severity only for migraine rows; keep None if no migraines that week
            func.avg(
                case(
                    (base_q.c.event_type == EventType.migraine, cast(base_q.c.severity, Float)),
                    else_=None
                )
            ).label('migraine_avg_severity'),

            # sums for sleep/stress/meals
            func.sum(
                case(
                    (base_q.c.event_type == EventType.sleep,  base_q.c.value_std),
                    else_=0.0
                )
            ).label('sleep_hours'),
            func.sum(
                case(
                    (base_q.c.event_type == EventType.stress, base_q.c.value_std),
                    else_=0.0
                )
            ).label('stress_hours'),
            func.sum(
                case(
                    (base_q.c.event_type == EventType.meals,  base_q.c.value_std),
                    else_=0.0
                )
            ).label('meals_count'),
        )
        .group_by(base_q.c.week_start_monday)
        .order_by(base_q.c.week_start_monday)
    )

    rows = weekly_q.all()
    if not rows:
        return []

    # --- Build continuous week calendar in Python ---
    def to_date(s: str) -> datetime:
        return datetime.strptime(s, "%Y-%m-%d")

    def align_to_monday(d: datetime) -> datetime:
        # Align to Monday of the same "current week" per Option B: next Monday then -7 days
        return (d + timedelta(days=(7 - d.weekday()) % 7)) - timedelta(days=7)

    min_week = to_date(rows[0].week_start_monday)
    max_week = to_date(rows[-1].week_start_monday)

    if start_date:
        sd = align_to_monday(to_date(start_date))
        min_week = min(sd, min_week)
    if end_date:
        ed = align_to_monday(to_date(end_date))
        max_week = max(ed, max_week)

    # Generate continuous weeks
    weeks = []
    cur = min_week
    while cur <= max_week:
        weeks.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=7)

    # Map sparse → continuous
    sparse = {r.week_start_monday: r for r in rows}
    series = []
    for w in weeks:
        r = sparse.get(w)
        series.append({
            "week_start_monday": w,
            "migraine_events": int(r.migraine_events) if r else 0,
            "migraine_avg_severity": float(r.migraine_avg_severity) if (r and r.migraine_avg_severity is not None) else None,
            "sleep_hours": float(r.sleep_hours) if r else 0.0,
            "stress_hours": float(r.stress_hours) if r else 0.0,
            "meals_count": float(r.meals_count) if r else 0.0,
        })

    # --- Lags, percent changes, moving averages ---
    def pct_change(curr, prev):
        if prev is None or prev == 0:
            return None
        return (curr - prev) / prev

    def moving_avg(values, k):
        out = []
        for i in range(len(values)):
            window = values[max(0, i - k + 1): i + 1]
            nums = [v for v in window if v is not None]
            out.append(sum(nums) / len(nums) if nums else None)
        return out

    k = max(window_size, 1)
    migraine_events = [x["migraine_events"] for x in series]
    migraine_sev    = [x["migraine_avg_severity"] for x in series]
    sleep_hours     = [x["sleep_hours"] for x in series]
    stress_hours    = [x["stress_hours"] for x in series]
    meals_count     = [x["meals_count"] for x in series]

    migraine_events_prev = [None] + migraine_events[:-1]
    migraine_sev_prev    = [None] + migraine_sev[:-1]
    sleep_hours_prev     = [None] + sleep_hours[:-1]
    stress_hours_prev    = [None] + stress_hours[:-1]
    meals_count_prev     = [None] + meals_count[:-1]

    pct_migraine_events_change   = [pct_change(c, p) for c, p in zip(migraine_events, migraine_events_prev)]
    pct_migraine_severity_change = [pct_change((c if c is not None else 0), (p if p is not None else 0)) for c, p in zip(migraine_sev, migraine_sev_prev)]
    pct_sleep_hours_change       = [pct_change(c, p) for c, p in zip(sleep_hours, sleep_hours_prev)]
    pct_stress_hours_change      = [pct_change(c, p) for c, p in zip(stress_hours, stress_hours_prev)]
    pct_meals_count_change       = [pct_change(c, p) for c, p in zip(meals_count, meals_count_prev)]

    ma_migraine_events   = moving_avg(migraine_events, k)
    ma_migraine_severity = moving_avg(migraine_sev, k)
    ma_sleep_hours       = moving_avg(sleep_hours, k)
    ma_stress_hours      = moving_avg(stress_hours, k)
    ma_meals_count       = moving_avg(meals_count, k)

    out = []
    for i, row in enumerate(series):
        out.append({
            **row,
            "migraine_events_prev": migraine_events_prev[i],
            "migraine_severity_prev": migraine_sev_prev[i],
            "sleep_hours_prev": sleep_hours_prev[i],
            "stress_hours_prev": stress_hours_prev[i],
            "meals_count_prev": meals_count_prev[i],

            "pct_migraine_events_change": pct_migraine_events_change[i],
            "pct_migraine_severity_change": pct_migraine_severity_change[i],
            "pct_sleep_hours_change": pct_sleep_hours_change[i],
            "pct_stress_hours_change": pct_stress_hours_change[i],
            "pct_meals_count_change": pct_meals_count_change[i],

            "moving_average_migraine_events": ma_migraine_events[i],
            "moving_average_migraine_severity": ma_migraine_severity[i],
            "moving_average_sleep_hours": ma_sleep_hours[i],
            "moving_average_stress_hours": ma_stress_hours[i],
            "moving_average_meals_count": ma_meals_count[i],
        })

    return out


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
    start_date = date(2025, 9, 30)
    end_date =  date(2025, 11, 3)
    for id in user_map.values():
        num_migraine_events = 10
        num_sleep_events = random.randint(3, 12)
        num_stress_events = random.randint(4, 18)
        num_meal_events = random.randint(3, 6)
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
                event_timestamp=get_random_date_between(start_date, end_date),
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
                event_timestamp=get_random_date_between(start_date, end_date),
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
                event_timestamp=get_random_date_between(start_date, end_date),
                creation_timestamp=get_random_date_between(start_date, end_date))
            db.add(s)
        for _ in range(num_meal_events):
            s = Event(user_id=id,
                system=VARS['mealSystem'],
                code=VARS['mealCode'],
                event_type=EventType.meals,
                numerical_value=random.randint(1, 3),
                numerical_unit=Unit.number,
                description='Had some meals today',
                event_timestamp=get_random_date_between(start_date, end_date),
                creation_timestamp=get_random_date_between(start_date, end_date))
            db.add(s)
    db.commit()
    return {'status': "OK"}


@app.get("/api/populate_large", status_code=200)
async def populate_large_data(
    db: Session = Depends(get_db),
    days: int = Query(56, ge=7, le=365, description="Number of days to populate (default 56 = 8 weeks)."),
    seed: int | None = Query(42, description="Optional random seed for reproducibility."),
    reset: bool = Query(False, description="If true, delete existing events in the generated date range for these users before repopulating.")
):
    """
    Populate synthetic data for 4 users as a *daily record log* with randomness and plausible correlations:
      - Every day: 1 sleep (hours), 1 stress (hours + severity), 1 meals row (count=2..4)
      - 0–2 migraines per day; probability & severity biased by low sleep / high stress
      - Units match weekly aggregation logic (sleep/stress in hours, meals count, migraine minutes+severity)

    Query params:
      - days: integer number of days to populate (default 56)
      - seed: RNG seed (default 42; set None for non-reproducible randomness)
      - reset: delete existing events in the date range for these users before inserting
    """

    # --- Randomness control ---
    if seed is not None:
        random.seed(seed)

    # --- Create or reuse users ---
    names = ['Jessica', 'Albert', 'John', 'Susan']
    users: list[User] = []
    for n in names:
        existing = db.query(User).filter(User.name == n).first()
        if existing:
            users.append(existing)
        else:
            u = User(name=n)
            db.add(u)
            db.flush()
            users.append(u)

    user_ids = [u.id for u in users]

    # --- Date range (last `days` days including today) ---
    today = date.today()
    start_date = today - timedelta(days=days - 1)
    end_date = today

    # --- Optional reset: delete existing events in range for these users ---
    if reset:
        for uid in user_ids:
            db.query(Event).filter(
                Event.user_id == uid,
                and_(
                    Event.event_timestamp >= datetime.combine(start_date, time.min),
                    Event.event_timestamp <= datetime.combine(end_date, time.max),
                )
            ).delete(synchronize_session=False)
        db.flush()

    # --- Helpers for random but plausible daily logs ---
    def dt_at(day: date, hour: int, minute: int = 0) -> datetime:
        return datetime.combine(day, time(hour=hour, minute=minute))

    def sample_sleep_hours() -> float:
        # 6–9 hours, uniform with rounding to 0.1h for variability
        return round(random.uniform(6.0, 9.0), 1)

    def sample_stress_hours() -> float:
        # Gaussian around ~2.5h (σ=1.5), clipped to [0, 6], rounded
        val = max(0.0, min(6.0, random.gauss(2.5, 1.5)))
        return round(val, 1)

    def sample_severity_stress() -> Severity:
        # Weighted: favor low/med, occasional high peaks
        weights = [0.25, 0.25, 0.25, 0.15, 0.10]  # low .. high
        return random.choices(list(Severity), weights=weights, k=1)[0]

    def migraine_probability(sleep_hours: float, stress_hours: float, stress_sev: Severity) -> float:
        # Base 0.15; bumps with low sleep / high stress / high severity; capped at 0.6
        p = 0.15
        if sleep_hours < 6.0:
            p += 0.10
        if stress_hours > 3.0:
            p += 0.10
        if stress_sev >= Severity.med_high:
            p += 0.05
        return min(max(p, 0.0), 0.6)

    def sample_migraine_severity(sleep_hours: float, stress_hours: float, stress_sev: Severity) -> Severity:
        # Increase severity mass under low sleep/high stress/high stress severity
        bias = 0
        if sleep_hours < 6.0:
            bias += 1
        if stress_hours > 3.0:
            bias += 1
        if stress_sev >= Severity.med_high:
            bias += 1
        base_weights = [0.30, 0.25, 0.25, 0.12, 0.08]  # low..high
        for _ in range(bias):
            base_weights = [
                max(w - 0.03, 0.01) if i < 2 else min(w + 0.03, 0.60)
                for i, w in enumerate(base_weights)
            ]
        total = sum(base_weights)
        weights = [w / total for w in base_weights]
        return random.choices(list(Severity), weights=weights, k=1)[0]

    def sample_migraine_duration_minutes(sev: Severity) -> int:
        # Duration loosely correlated with severity
        ranges = {
            Severity.low:      (10, 40),
            Severity.low_med:  (20, 60),
            Severity.med:      (30, 90),
            Severity.med_high: (40, 120),
            Severity.high:     (60, 180),
        }
        return random.randint(*ranges[sev])

    # --- Populate per user per day ---
    for uid in user_ids:
        day = start_date
        while day <= end_date:
            # Sleep
            sleep_hours = sample_sleep_hours()
            sleep_event = Event(
                user_id=uid,
                system=VARS['sleepSystem'],
                code=VARS['sleepCode'],
                event_type=EventType.sleep,
                numerical_value=int(round(sleep_hours)),  # store integer hours
                numerical_unit=Unit.hours,
                description=f"Sleep duration: {sleep_hours}h",
                event_timestamp=dt_at(day, 23, random.randint(0, 59)),
                creation_timestamp=dt_at(day, 23, 59)
            )
            db.add(sleep_event)

            # Stress
            stress_hours = sample_stress_hours()
            stress_sev = sample_severity_stress()
            stress_event = Event(
                user_id=uid,
                system=VARS['stressSystem'],
                code=VARS['stressCode'],
                event_type=EventType.stress,
                severity=stress_sev,
                numerical_value=int(round(stress_hours)),
                numerical_unit=Unit.hours,
                description=f"Stress exposure: {stress_hours}h, severity {int(stress_sev)}",
                event_timestamp=dt_at(day, 16, random.randint(0, 59)),
                creation_timestamp=dt_at(day, 16, 59)
            )
            db.add(stress_event)

            # Meals (ONE ROW per day): random count 2..4
            meals_count = random.randint(2, 4)
            # Use a midday timestamp with slight jitter; count stored in numerical_value
            meal_event = Event(
                user_id=uid,
                system=VARS['mealSystem'],
                code=VARS['mealCode'],
                event_type=EventType.meals,
                numerical_value=meals_count,
                numerical_unit=Unit.number,
                description=f"Meals eaten: {meals_count}",
                event_timestamp=dt_at(day, 12, random.randint(0, 30)),
                creation_timestamp=dt_at(day, 12, random.randint(0, 30))
            )
            db.add(meal_event)

            # Migraines (0–2 per day with correlated probability)
            p = migraine_probability(sleep_hours, stress_hours, stress_sev)
            occurrences = 0
            if random.random() < p:
                occurrences += 1
            if random.random() < (p / 2.0):
                occurrences += 1

            for k in range(occurrences):
                mig_sev = sample_migraine_severity(sleep_hours, stress_hours, stress_sev)
                duration_min = sample_migraine_duration_minutes(mig_sev)
                base_hour = 10 if k == 0 else 19  # stagger morning/evening
                migraine_event = Event(
                    user_id=uid,
                    system=VARS['migraineSystem'],
                    code=VARS['migraineCode'],
                    event_type=EventType.migraine,
                    severity=mig_sev,
                    numerical_value=duration_min,
                    numerical_unit=Unit.minutes,
                    description=f"Migraine ({int(mig_sev)}), {duration_min} minutes",
                    event_timestamp=dt_at(day, base_hour, random.randint(0, 59)),
                    creation_timestamp=dt_at(day, base_hour, 59)
                )
                db.add(migraine_event)

            day += timedelta(days=1)

    db.commit()

    return {
        "status": "OK",
        "users": names,
        "start_date": str(start_date),
        "end_date": str(end_date),
        "days_populated": days,
        "reset": reset,
        "seed": seed
    }


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if ".." in full_path:
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(os.path.join(DIST_DIR, "index.html"))

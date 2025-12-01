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

from sqlalchemy import func, cast, String, Float, case, and_
from fastapi import Query, Depends
from datetime import datetime, timedelta, date, time

from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.observation import Observation
from fhirclient.models.encounter import Encounter
from fhirclient.models.fhirreference import FHIRReference
from fhirclient.models.bundle import Bundle

Base.metadata.create_all(bind=engine)

VARS = {
    'migraineSystem': 'LOINC',
    'migraineCode': 'LA15141-7',
    'sleepSystem': 'ICD-10',
    'sleepCode': 'Y93.84',
    'stressSystem': 'ICD-10',
    'stressCode': 'Z73.3',
    'mealSystem': 'ICD-10',
    'mealCode': 'Y93.G1',
    'exerciseSystem': 'ICD-10',
    'exerciseCode': 'Y93.A9',
    'medicationSystem': 'ICD-10',
    'medicationCode': 'Z79.899'
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


def default_system_code_for(event_type: EventType) -> tuple[str, str]:
    if event_type == EventType.migraine:
        return VARS['migraineSystem'], VARS['migraineCode']
    if event_type == EventType.sleep:
        return VARS['sleepSystem'], VARS['sleepCode']
    if event_type == EventType.stress:
        return VARS['stressSystem'], VARS['stressCode']
    if event_type == EventType.meals:
        return VARS['mealSystem'], VARS['mealCode']
    if event_type == EventType.exercise:
        return VARS['exerciseSystem'], VARS['exerciseCode']
    if event_type == EventType.medication:
        return VARS['medicationSystem'], VARS['medicationCode']
    # fallback
    return ("LOCAL", event_type.value.upper())


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
    payload = event_request.model_dump()
    # If system/code not provided, fill from VARS based on event_type
    if not payload.get("system") or not payload.get("code"):
        sys, code = default_system_code_for(payload["event_type"])
        payload["system"] = payload.get("system") or sys
        payload["code"] = payload.get("code") or code
    new_event = Event(user_id=user_id, **payload)

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
    # Empty check (ORM binds GUID/BLOB correctly)
    total_events = (
        db.query(func.count(Event.id))
          .filter(Event.user_id == user_id)
          .scalar()
    )
    if not total_events:
        return []

    # Week bucket (Option B)
    ts_text = cast(Event.event_timestamp, String)
    ts_norm = func.replace(ts_text, 'T', ' ')
    week_start = func.date(ts_norm, 'localtime', 'weekday 1', '-7 days') if use_localtime \
                 else func.date(ts_norm, 'weekday 1', '-7 days')

    # Normalize numeric metrics (sleep -> hours; meals -> count). Stress excluded.
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
            and_(Event.event_type == EventType.meals,  Event.numerical_unit == Unit.number),
            cast(Event.numerical_value, Float)
        ),
        (
            and_(Event.event_type == EventType.exercise, Event.numerical_unit == Unit.number),
            cast(Event.numerical_value, Float)
        ),
        (
            and_(Event.event_type == EventType.medication, Event.numerical_unit == Unit.number),
            cast(Event.numerical_value, Float)
        ),

        else_=None
    )

    base_q = (
        db.query(
            week_start.label('week_start_monday'),
            Event.event_type.label('event_type'),
            Event.severity.label('severity'),
            value_std.label('value_std')
        )
        .filter(Event.user_id == user_id, Event.event_timestamp.isnot(None))
    ).subquery()

    weekly_q = (
        db.query(
            base_q.c.week_start_monday,

            # migraines
            func.sum(case((base_q.c.event_type == EventType.migraine, 1), else_=0)).label('migraine_events'),
            func.avg(case((base_q.c.event_type == EventType.migraine, cast(base_q.c.severity, Float)), else_=None)).label('migraine_avg_severity'),

            # sleep hours
            func.sum(case((base_q.c.event_type == EventType.sleep, base_q.c.value_std), else_=0.0)).label('sleep_hours'),

            func.sum(case((base_q.c.event_type == EventType.stress, 1), else_=0)).label('stress_events'),
            func.avg(case((base_q.c.event_type == EventType.stress, cast(base_q.c.severity, Float)), else_=None)).label('stress_avg_severity'),

            # meals count
            func.sum(case((base_q.c.event_type == EventType.meals, base_q.c.value_std), else_=0.0)).label('meals_count'),

            # exercise
            func.sum(case((base_q.c.event_type == EventType.exercise, base_q.c.value_std), else_=0.0)).label('exercise_days'),
            # medication
            func.sum(case((base_q.c.event_type == EventType.medication, base_q.c.value_std), else_=0.0)).label('medication_days'),

        )
        .group_by(base_q.c.week_start_monday)
        .order_by(base_q.c.week_start_monday)
    )

    rows = weekly_q.all()
    if not rows:
        return []

    # Continuous week calendar
    def to_date(s: str) -> datetime:
        return datetime.strptime(s, "%Y-%m-%d")

    def align_to_monday(d: datetime) -> datetime:
        return (d + timedelta(days=(7 - d.weekday()) % 7)) - timedelta(days=7)

    min_week = to_date(rows[0].week_start_monday)
    max_week = to_date(rows[-1].week_start_monday)
    if start_date:
        sd = align_to_monday(to_date(start_date)); min_week = min(sd, min_week)
    if end_date:
        ed = align_to_monday(to_date(end_date));    max_week = max(ed, max_week)

    weeks, cur = [], min_week
    while cur <= max_week:
        weeks.append(cur.strftime("%Y-%m-%d"))
        cur += timedelta(days=7)

    sparse = {r.week_start_monday: r for r in rows}
    series = []
    for w in weeks:
        r = sparse.get(w)
        series.append({
            "week_start_monday": w,
            "migraine_events": int(r.migraine_events) if r else 0,
            "migraine_avg_severity": float(r.migraine_avg_severity) if (r and r.migraine_avg_severity is not None) else None,
            "sleep_hours": float(r.sleep_hours) if r else 0.0,
            "stress_events": int(r.stress_events) if r else 0,
            "stress_avg_severity": float(r.stress_avg_severity) if (r and r.stress_avg_severity is not None) else None,
            "meals_count": float(r.meals_count) if r else 0.0,
            "exercise_days": float(r.exercise_days) if r else 0.0,
            "medication_days": float(r.medication_days) if r else 0.0,

        })

    # Lags / pct changes / moving averages
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
    migraine_events  = [x["migraine_events"]       for x in series]
    migraine_sev     = [x["migraine_avg_severity"] for x in series]
    sleep_hours      = [x["sleep_hours"]           for x in series]
    stress_events    = [x["stress_events"]         for x in series]
    stress_sev       = [x["stress_avg_severity"]   for x in series]
    meals_count      = [x["meals_count"]           for x in series]
    exercise_days = [x["exercise_days"] for x in series]
    medication_days = [x["medication_days"] for x in series]

    migraine_events_prev = [None] + migraine_events[:-1]
    migraine_sev_prev    = [None] + migraine_sev[:-1]
    sleep_hours_prev     = [None] + sleep_hours[:-1]
    stress_events_prev   = [None] + stress_events[:-1]
    stress_sev_prev      = [None] + stress_sev[:-1]
    meals_count_prev     = [None] + meals_count[:-1]
    exercise_days_prev   = [None] + exercise_days[:-1]
    medication_days_prev = [None] + medication_days[:-1]

    pct_migraine_events_change   = [pct_change(c, p) for c, p in zip(migraine_events, migraine_events_prev)]
    pct_migraine_severity_change = [pct_change((c if c is not None else 0), (p if p is not None else 0)) for c, p in zip(migraine_sev, migraine_sev_prev)]
    pct_sleep_hours_change       = [pct_change(c, p) for c, p in zip(sleep_hours, sleep_hours_prev)]
    pct_stress_events_change     = [pct_change(c, p) for c, p in zip(stress_events, stress_events_prev)]
    pct_stress_severity_change   = [pct_change((c if c is not None else 0), (p if p is not None else 0)) for c, p in zip(stress_sev, stress_sev_prev)]
    pct_meals_count_change       = [pct_change(c, p) for c, p in zip(meals_count, meals_count_prev)]
    pct_exercise_days_change     = [pct_change(c, p) for c, p in zip(exercise_days, exercise_days_prev)]
    pct_medication_days_change   = [pct_change(c, p) for c, p in zip(medication_days, medication_days_prev)]

    ma_migraine_events   = moving_avg(migraine_events, k)
    ma_migraine_severity = moving_avg(migraine_sev, k)
    ma_sleep_hours       = moving_avg(sleep_hours, k)
    ma_stress_events     = moving_avg(stress_events, k)
    ma_stress_severity   = moving_avg(stress_sev, k)
    ma_meals_count       = moving_avg(meals_count, k)
    ma_exercise_days     = moving_avg(exercise_days, k)
    ma_medication_days   = moving_avg(medication_days, k)

    out = []
    for i, row in enumerate(series):
        out.append({
            **row,
            "migraine_events_prev": migraine_events_prev[i],
            "migraine_severity_prev": migraine_sev_prev[i],
            "sleep_hours_prev": sleep_hours_prev[i],
            "stress_events_prev": stress_events_prev[i],
            "stress_severity_prev": stress_sev_prev[i],
            "meals_count_prev": meals_count_prev[i],
            "exercise_days_prev": exercise_days_prev[i],
            "medication_days_prev": medication_days_prev[i],

            "pct_migraine_events_change": pct_migraine_events_change[i],
            "pct_migraine_severity_change": pct_migraine_severity_change[i],
            "pct_sleep_hours_change": pct_sleep_hours_change[i],
            "pct_stress_events_change": pct_stress_events_change[i],
            "pct_stress_severity_change": pct_stress_severity_change[i],
            "pct_meals_count_change": pct_meals_count_change[i],
            "pct_exercise_days_change": pct_exercise_days_change[i],
            "pct_medication_days_change": pct_medication_days_change[i],

            "moving_average_migraine_events": ma_migraine_events[i],
            "moving_average_migraine_severity": ma_migraine_severity[i],
            "moving_average_sleep_hours": ma_sleep_hours[i],
            "moving_average_stress_events": ma_stress_events[i],
            "moving_average_stress_severity": ma_stress_severity[i],
            "moving_average_meals_count": ma_meals_count[i],
            "moving_average_exercise_days": ma_exercise_days[i],
            "moving_average_medication_days": ma_medication_days[i],

        })
    return out


@app.get("/api/action-items")
async def get_action_items(
    db: db_dependency,
    user_id: str,
    window_size: int = Query(2, ge=1, le=26, description="Weeks in current period (default 2)."),
    use_localtime: bool = Query(False, description="Apply SQLite 'localtime' before week bucketing."),
    min_sleep_hours: float = Query(7.0, description="Target average sleep hours/day."),
    min_meals_per_day: float = Query(3.0, description="Target average meals/day."),
    stress_severity_threshold: float = Query(3.0, description="Threshold for avg stress severity."),
    min_exercise_days: int = Query(3, description="Target number of exercise days per week.")
):
    # Week bucketing
    ts_text = cast(Event.event_timestamp, String)
    ts_norm = func.replace(ts_text, 'T', ' ')
    week_start = func.date(ts_norm, 'localtime', 'weekday 1', '-7 days') if use_localtime \
                 else func.date(ts_norm, 'weekday 1', '-7 days')

    # Normalize numeric metrics (sleep hours, meals count) — stress excluded
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
            and_(Event.event_type == EventType.meals,  Event.numerical_unit == Unit.number),
            cast(Event.numerical_value, Float)
        ),
        (
            and_(Event.event_type == EventType.exercise, Event.numerical_unit == Unit.number),
            cast(Event.numerical_value, Float)
        ),
        else_=None
    )

    base_q = (
        db.query(
            week_start.label('week_start_monday'),
            Event.event_type.label('event_type'),
            Event.severity.label('severity'),
            value_std.label('value_std')
        )
        .filter(Event.user_id == user_id, Event.event_timestamp.isnot(None))
    ).subquery()

    weekly_q = (
        db.query(
            base_q.c.week_start_monday,
            func.sum(case((base_q.c.event_type == EventType.migraine, 1), else_=0)).label('migraine_events'),
            func.avg(case((base_q.c.event_type == EventType.migraine, cast(base_q.c.severity, Float)), else_=None)).label('migraine_avg_severity'),
            func.sum(case((base_q.c.event_type == EventType.sleep,  base_q.c.value_std), else_=0.0)).label('sleep_hours'),
            func.sum(case((base_q.c.event_type == EventType.stress, 1), else_=0)).label('stress_events'),
            func.avg(case((base_q.c.event_type == EventType.stress, cast(base_q.c.severity, Float)), else_=None)).label('stress_avg_severity'),
            func.sum(case((base_q.c.event_type == EventType.meals,  base_q.c.value_std), else_=0.0)).label('meals_count'),
            func.sum(case((base_q.c.event_type == EventType.exercise, base_q.c.value_std), else_=0.0)).label('exercise_days'),
        )
        .group_by(base_q.c.week_start_monday)
        .order_by(base_q.c.week_start_monday)
    )

    weekly = weekly_q.all()
    if not weekly:
        return {"user_id": user_id, "action_items": [], "summary": {"message": "No data found for user."}}

    # Current vs previous
    current  = weekly[-window_size:] if len(weekly) >= window_size else weekly[:]
    previous = weekly[-(2*window_size):-window_size] if len(weekly) >= 2*window_size else []

    def avg_per_day_from_weeks(values):
        if not values: return None
        return sum(values) / (7 * len(values))

    def avg_across_weeks(values):
        nums = [v for v in values if v is not None]
        return (sum(nums) / len(nums)) if nums else None

    # Current
    cur_sleep_per_day   = avg_per_day_from_weeks([w.sleep_hours for w in current])
    cur_meals_per_day   = avg_per_day_from_weeks([w.meals_count for w in current])
    cur_stress_severity = avg_across_weeks([w.stress_avg_severity for w in current])
    cur_mig_events_per_week = (sum([w.migraine_events for w in current]) / len(current)) if current else None
    cur_mig_severity        = avg_across_weeks([w.migraine_avg_severity for w in current])
    cur_exercise_per_day = avg_per_day_from_weeks([w.exercise_days for w in current])
    cur_exercise_days_total = sum([w.exercise_days for w in current])

    # Previous
    prev_sleep_per_day       = avg_per_day_from_weeks([w.sleep_hours for w in previous]) if previous else None
    prev_meals_per_day       = avg_per_day_from_weeks([w.meals_count for w in previous]) if previous else None
    prev_stress_severity     = avg_across_weeks([w.stress_avg_severity for w in previous]) if previous else None
    prev_mig_events_per_week = (sum([w.migraine_events for w in previous]) / len(previous)) if previous else None
    prev_mig_severity        = avg_across_weeks([w.migraine_avg_severity for w in previous]) if previous else None
    prev_exercise_per_day    = avg_per_day_from_weeks([w.exercise_days for w in previous]) if previous else None


    def pct_change(cur, prev):
        if cur is None or prev is None or prev == 0: return None
        return (cur - prev) / prev

    sleep_pct_change      = pct_change(cur_sleep_per_day, prev_sleep_per_day)
    meals_pct_change      = pct_change(cur_meals_per_day, prev_meals_per_day)
    stress_pct_change     = pct_change(cur_stress_severity, prev_stress_severity)
    mig_events_change     = pct_change(cur_mig_events_per_week, prev_mig_events_per_week)
    mig_severity_change   = pct_change(cur_mig_severity, prev_mig_severity)
    exercise_pct_change   = pct_change(cur_exercise_per_day, prev_exercise_per_day)


    actions = []
    if cur_sleep_per_day is not None and cur_sleep_per_day < min_sleep_hours:
        actions.append({
            "title": "Get more sleep",
            "priority": "high" if (sleep_pct_change is not None and sleep_pct_change < -0.1) else "medium",
            "reason": f"Average sleep is {cur_sleep_per_day:.2f}h/day over {len(current)} weeks, below target {min_sleep_hours:.1f}h/day."
                      + (f" Down {abs(sleep_pct_change*100):.1f}% vs previous period." if sleep_pct_change and sleep_pct_change < 0 else "")
        })

    if cur_meals_per_day is not None and cur_meals_per_day < min_meals_per_day:
        actions.append({
            "title": "Have more meals",
            "priority": "medium",
            "reason": f"Average meals are {cur_meals_per_day:.2f}/day, below target {min_meals_per_day:.1f}/day."
                      + (f" Down {abs(meals_pct_change*100):.1f}% vs previous period." if meals_pct_change and meals_pct_change < 0 else "")
        })

    stress_high   = (cur_stress_severity is not None and cur_stress_severity >= stress_severity_threshold)
    stress_rising = (stress_pct_change is not None and stress_pct_change > 0.10)
    if stress_high or stress_rising:
        detail = []
        if stress_high:
            detail.append(f"avg stress severity is {cur_stress_severity:.2f} (target ≤ {stress_severity_threshold:.1f})")
        if stress_rising:
            detail.append(f"stress severity up {stress_pct_change*100:.1f}% vs previous period")
        actions.append({
            "title": "Reduce stress using healthy methods",
            "priority": "high" if stress_high and stress_rising else "medium",
            "reason": " ; ".join(detail)
        })

    if cur_exercise_per_day is not None and cur_exercise_days_total < (min_exercise_days * len(current)):
        actions.append({
            "title": "Exercise more regularly",
            "priority": "medium",
            "reason": f"Exercised on {cur_exercise_days_total} days over {len(current)} weeks, below target {min_exercise_days * len(current)} days."
        })

    migraine_context = {}
    if cur_mig_events_per_week is not None:
        migraine_context["migraine_events_per_week"] = round(cur_mig_events_per_week, 2)
    if cur_mig_severity is not None:
        migraine_context["migraine_avg_severity"] = round(cur_mig_severity, 2)
    if mig_events_change is not None:
        migraine_context["migraine_events_change_pct"] = round(mig_events_change * 100, 1)
    if mig_severity_change is not None:
        migraine_context["migraine_severity_change_pct"] = round(mig_severity_change * 100, 1)

    summary = {
        "period_weeks": len(current),
        "sleep_hours_per_day": cur_sleep_per_day,
        "meals_per_day": cur_meals_per_day,
        "stress_avg_severity": cur_stress_severity, 
        "exercise_per_day": cur_exercise_per_day,
        "previous_period": {
            "exists": bool(previous),
            "sleep_hours_per_day": prev_sleep_per_day,
            "meals_per_day": prev_meals_per_day,
            "stress_avg_severity": prev_stress_severity,
        },
        "percent_changes": {
            "sleep": sleep_pct_change,
            "meals": meals_pct_change,
            "stress_severity": stress_pct_change,
            "migraine_events": mig_events_change,
            "migraine_severity": mig_severity_change,
            "exercise": exercise_pct_change,
        },
        "migraine_context": migraine_context,
        "bucket_range": {
            "start_week": weekly[0].week_start_monday,
            "end_week": weekly[-1].week_start_monday
        }
    }

    return {
        "user_id": user_id,
        "action_items": actions,
        "summary": summary
    }


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
async def export_patient_data_to_fhir(
    db: db_dependency,
    user_id: str,
    chunk_size: int = Query(75, ge=1, le=250, description="Max Observation entries per batch POST.")
):
    """
    Export all of a user's data to the demo HAPI FHIR server using FHIR Bundle(type='batch').
    1) Create or reuse Patient.
    2) POST Observations in chunked batch Bundles to reduce HTTP calls.
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

    # -- Create or reuse Patient on server
    patient_resource: Patient = convert_user_to_fhir(user)
    existing_patients = Patient.where(struct={'identifier': user_id}).perform_resources(smart.server)
    if existing_patients:
        patient_json = existing_patients[0].as_json()
        patient_id = patient_json['id']
        reused = True
    else:
        created_patient_json = patient_resource.create(smart.server)  # POST /Patient
        patient_id = created_patient_json['id']
        reused = False

    # -- Convert Events -> Observation JSON; link to Patient
    obs_jsons: List[Dict[str, Any]] = []
    for ev in events:
        try:
            obs: Observation = convert_event_to_fhir(ev)
            obs.subject = FHIRReference({'reference': f'Patient/{patient_id}'})
            obs_jsons.append(obs.as_json())
        except Exception:
            continue

    created_obs_locations: List[str] = []
    errors: List[Dict[str, Any]] = []

    # -- Helper to POST batch bundle in one HTTP request
    def post_batch(entries: List[Dict[str, Any]]):
        bundle = Bundle({'type': 'batch', 'entry': entries})
        # Explicitly set headers for FHIR JSON
        return smart.server.session.post(
            smart.server.base_uri,
            headers={"Content-Type": "application/fhir+json"},
            json=bundle.as_json()
        )

    # -- Chunk and POST
    for i in range(0, len(obs_jsons), chunk_size):
        chunk = obs_jsons[i:i + chunk_size]
        entries = [
            {
                'resource': obs,
                'request': {'method': 'POST', 'url': 'Observation'}
            } for obs in chunk
        ]
        try:
            resp = post_batch(entries)
            resp_text = resp.text.strip()
            resp_json = resp.json() if resp_text else {}

            if not resp_json or 'entry' not in resp_json:
                errors.append({
                    "error": "Empty or invalid response from FHIR server",
                    "status_code": resp.status_code,
                    "raw_text": resp_text[:200]
                })
                continue

            for entry in resp_json.get('entry', []):
                r = entry.get('response', {})
                status = r.get('status', '')
                location = r.get('location')
                if status.startswith('201') and location:
                    created_obs_locations.append(location)
                else:
                    errors.append({'status': status, 'outcome': r.get('outcome')})
        except Exception as e:
            errors.append({'error': str(e)})

    return {
        "ok": True,
        "patient": {
            "id": patient_id,
            "reused": reused,
            "identifiers": [iden for iden in (patient_json.get('identifier') if reused else (created_patient_json.get('identifier') or []))]
        },
        "observations": {
            "created_count": len(created_obs_locations),
            "locations": created_obs_locations
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
    if seed is not None:
        random.seed(seed)

    names = ['Jessica', 'Albert', 'John', 'Susan']
    users: list[User] = []
    for n in names:
        existing = db.query(User).filter(User.name == n).first()
        users.append(existing if existing else User(name=n))
        if not existing:
            db.add(users[-1]); db.flush()
    user_ids = [u.id for u in users]

    today = date.today()
    start_date = today - timedelta(days=days - 1)
    end_date = today

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

    def dt_at(day: date, hour: int, minute: int = 0) -> datetime:
        return datetime.combine(day, time(hour=hour, minute=minute))

    def sample_sleep_hours() -> float:
        return round(random.uniform(6.0, 9.0), 1)

    def sample_severity_stress() -> Severity:
        # Weighted: favor low/med, occasional high
        weights = [0.25, 0.25, 0.25, 0.15, 0.10]  # low..high
        return random.choices(list(Severity), weights=weights, k=1)[0]

    def migraine_probability(sleep_hours: float, stress_sev: Severity) -> float:
        p = 0.15
        if sleep_hours < 6.0: p += 0.10
        if stress_sev >= Severity.med_high: p += 0.10
        return min(max(p, 0.0), 0.6)

    def sample_migraine_severity(sleep_hours: float, stress_sev: Severity) -> Severity:
        bias = 0
        if sleep_hours < 6.0: bias += 1
        if stress_sev >= Severity.med_high: bias += 1
        base = [0.30, 0.25, 0.25, 0.12, 0.08]
        for _ in range(bias):
            base = [max(w - 0.03, 0.01) if i < 2 else min(w + 0.03, 0.60) for i, w in enumerate(base)]
        s = sum(base); weights = [w/s for w in base]
        return random.choices(list(Severity), weights=weights, k=1)[0]

    def sample_migraine_duration_minutes(sev: Severity) -> int:
        ranges = {
            Severity.low:      (10, 40),
            Severity.low_med:  (20, 60),
            Severity.med:      (30, 90),
            Severity.med_high: (40, 120),
            Severity.high:     (60, 180),
        }
        return random.randint(*ranges[sev])

    for uid in user_ids:
        day = start_date
        while day <= end_date:
            # Sleep (hours per day)
            sleep_hours = sample_sleep_hours()
            db.add(Event(
                user_id=uid,
                system=VARS['sleepSystem'],
                code=VARS['sleepCode'],
                event_type=EventType.sleep,
                numerical_value=int(round(sleep_hours)),
                numerical_unit=Unit.hours,
                description=f"Sleep duration: {sleep_hours}h",
                event_timestamp=dt_at(day, 23, random.randint(0, 59)),
                creation_timestamp=dt_at(day, 23, 59)
            ))

            stress_sev = sample_severity_stress()
            db.add(Event(
                user_id=uid,
                system=VARS['stressSystem'],
                code=VARS['stressCode'],
                event_type=EventType.stress,
                severity=stress_sev,
                description=f"Daily stress rating: {int(stress_sev)}",
                event_timestamp=dt_at(day, 16, random.randint(0, 59)),
                creation_timestamp=dt_at(day, 16, 59)
            ))

            # Meals (one row/day; count 2..4)
            meals_count = random.randint(2, 4)
            db.add(Event(
                user_id=uid,
                system=VARS['mealSystem'],
                code=VARS['mealCode'],
                event_type=EventType.meals,
                numerical_value=meals_count,
                numerical_unit=Unit.number,
                description=f"Meals eaten: {meals_count}",
                event_timestamp=dt_at(day, 12, random.randint(0, 30)),
                creation_timestamp=dt_at(day, 12, random.randint(0, 30))
            ))

            # Migraines (0–2/day; depends on sleep + stress severity)
            p = migraine_probability(sleep_hours, stress_sev)
            occurrences = (1 if random.random() < p else 0) + (1 if random.random() < (p/2.0) else 0)
            for k in range(occurrences):
                msev = sample_migraine_severity(sleep_hours, stress_sev)
                dur  = sample_migraine_duration_minutes(msev)
                base_hour = 10 if k == 0 else 19
                db.add(Event(
                    user_id=uid,
                    system=VARS['migraineSystem'],
                    code=VARS['migraineCode'],
                    event_type=EventType.migraine,
                    severity=msev,
                    numerical_value=dur,
                    numerical_unit=Unit.minutes,
                    description=f"Migraine ({int(msev)}), {dur} minutes",
                    event_timestamp=dt_at(day, base_hour, random.randint(0, 59)),
                    creation_timestamp=dt_at(day, base_hour, 59)
                ))
                # Exercise (Yes/No)
                exercised = 1 if random.random() < 0.6 else 0  # ~60% probability
                db.add(Event(
                    user_id=uid,
                    system=VARS['exerciseSystem'],
                    code=VARS['exerciseCode'],
                    event_type=EventType.exercise,
                    numerical_value=exercised,
                    numerical_unit=Unit.number,
                    description=f"Did exercise: {'Yes' if exercised else 'No'}",
                    event_timestamp=dt_at(day, 18, random.randint(0, 59)),
                    creation_timestamp=dt_at(day, 18, 59)
                ))

                # Medication (Yes/No)
                took_med = 1 if random.random() < 0.8 else 0  # ~80% probability
                db.add(Event(
                    user_id=uid,
                    system=VARS['medicationSystem'],
                    code=VARS['medicationCode'],
                    event_type=EventType.medication,
                    numerical_value=took_med,
                    numerical_unit=Unit.number,
                    description=f"Took medication: {'Yes' if took_med else 'No'}",
                    event_timestamp=dt_at(day, 9, random.randint(0, 59)),
                    creation_timestamp=dt_at(day, 9, 59)))

            day += timedelta(days=1)

    db.commit()
    return {
        "status": "OK", "users": names,
        "start_date": str(start_date), "end_date": str(end_date),
        "days_populated": days, "reset": reset, "seed": seed
    }


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")

app.mount("/assets", StaticFiles(directory=os.path.join(DIST_DIR, "assets")), name="assets")

@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    if ".." in full_path:
        raise HTTPException(status_code=404, detail="Not Found")
    return FileResponse(os.path.join(DIST_DIR, "index.html"))

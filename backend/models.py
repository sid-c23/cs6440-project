from typing import List
from .database import Base
from sqlalchemy import TIMESTAMP, Column, String, Text, Enum, Integer, ForeignKey, TypeDecorator
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import func
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
import enum


class IntEnumType(TypeDecorator):
    """Persist an IntEnum as INTEGER in the DB while exposing IntEnum in Python."""
    impl = Integer
    cache_ok = True

    def __init__(self, enumtype, *args, **kwargs):
        self.enumtype = enumtype
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        # Python -> DB
        if value is None:
            return None
        # Accept either an IntEnum or a raw integer
        return int(value)

    def process_result_value(self, value, dialect):
        # DB -> Python
        if value is None:
            return None
        return self.enumtype(value)


# Other classes
class Severity(enum.IntEnum):
    low = 1
    low_med = 2
    med = 3
    med_high = 4
    high = 5

class EventType(str, enum.Enum):
    migraine = 'migraine'
    stress = 'stress'
    sleep = 'sleep'
    meals = 'meal'
    exercise = 'exercise'
    medication = 'medication'

class Unit(str, enum.Enum):
    hours = 'hours'
    minutes = 'minutes'
    number = 'number' 
# End Other classes

# Model definitions

# App-specific definition of a user
class User(Base):
    __tablename__ = 'users'
    id = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
    name = Column(String, nullable=False)
    events: Mapped[List["Event"]] = relationship(back_populates="user")
    # Metadata
    creation_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

# Generic app-specific definition of any event used.
# All observations/symptoms/triggers/etc will be used
# as this event in the database.
# The API should implement custom serializers.
class Event(Base):
    __tablename__ = 'events'
    # Primary Keys
    system = Column(String, primary_key=True, nullable=False)
    code = Column(String, primary_key=True, nullable=False)
    event_type = Column('event_type', Enum(EventType), primary_key=True, nullable=False)
    id = Column(GUID, primary_key=True, default=GUID_DEFAULT_SQLITE)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete='CASCADE'))
    user: Mapped["User"] = relationship(back_populates="events")
    event_timestamp = Column(TIMESTAMP(timezone=False), nullable=True)
    # Data Columns
    # severity = Column('severity', Enum(Severity), nullable=True)
    severity = Column('severity', IntEnumType(Severity), nullable=True)
    numerical_value = Column(Integer, nullable=True)
    numerical_unit = Column('unit', Enum(Unit), nullable=True)
    description = Column(Text(length=200), nullable=True)
    # Metadata
    creation_timestamp = Column(TIMESTAMP(timezone=False), nullable=False, server_default=func.now())
    update_timestamp = Column(TIMESTAMP(timezone=False), nullable=False, server_default=func.now())

# End Model definitions


"""
SQL analysis:

user_id=replace('4eeebdc1-9e3f-4e0c-86ac-cceb22fc0287', '-', '')

SELECT
  date(REPLACE(event_timestamp, 'T', ' '), 'weekday 1', '-7 days') AS week_start_monday,
  COUNT(*) AS event_count,
  AVG(severity) AS avg_severity
FROM events
WHERE
user_id=replace('4eeebdc1-9e3f-4e0c-86ac-cceb22fc0287', '-', '')
  AND event_type = 'migraine'
GROUP BY week_start_monday
ORDER BY week_start_monday;


WITH base AS (
  SELECT
    date(REPLACE(event_timestamp, 'T', ' '), 'weekday 1', '-7 days') AS week_start_monday,
    event_type,
    severity,
    CASE
      WHEN event_type = 'sleep'  AND unit = 'minutes' THEN numerical_value / 60.0
      WHEN event_type = 'sleep'  AND unit = 'hours'   THEN CAST(numerical_value AS REAL)
      WHEN event_type = 'stress' AND unit = 'minutes' THEN numerical_value / 60.0
      WHEN event_type = 'stress' AND unit = 'hours'   THEN CAST(numerical_value AS REAL)
      WHEN event_type = 'meal'   AND unit = 'number'  THEN CAST(numerical_value AS REAL)
      ELSE NULL
    END AS value_std
  FROM events
  WHERE user_id=replace('4eeebdc1-9e3f-4e0c-86ac-cceb22fc0287', '-', '')
)
SELECT
  week_start_monday,

  -- migraines
  COUNT(CASE WHEN event_type = 'migraine' THEN 1 END)       AS migraine_events,
  AVG(CASE WHEN event_type = 'migraine' THEN severity END)  AS migraine_avg_severity,

  -- sleep (sum of hours)
  SUM(CASE WHEN event_type = 'sleep' THEN value_std END)    AS sleep_hours,

  -- stress (sum of hours)
  SUM(CASE WHEN event_type = 'stress' THEN value_std END)   AS stress_hours,

  -- meals (count)
  SUM(CASE WHEN event_type = 'meal' THEN value_std END)     AS meals_count
FROM base
GROUP BY week_start_monday
ORDER BY week_start_monday;



-- Build the weekly pivot first (as in #2), then add windows:
WITH weekly AS (
  WITH base AS (
    SELECT
      date(REPLACE(event_timestamp, 'T', ' '), 'weekday 1', '-7 days') AS week_start_monday,
      event_type,
      severity,
      CASE
        WHEN event_type = 'sleep'  AND unit = 'minutes' THEN numerical_value / 60.0
        WHEN event_type = 'sleep'  AND unit = 'hours'   THEN CAST(numerical_value AS REAL)
        WHEN event_type = 'stress' AND unit = 'minutes' THEN numerical_value / 60.0
        WHEN event_type = 'stress' AND unit = 'hours'   THEN CAST(numerical_value AS REAL)
        WHEN event_type = 'meal'   AND unit = 'number'  THEN CAST(numerical_value AS REAL)
        ELSE NULL
      END AS value_std
    FROM events
  WHERE user_id=replace('4eeebdc1-9e3f-4e0c-86ac-cceb22fc0287', '-', '')
  )
  SELECT
    week_start_monday,
    COUNT(CASE WHEN event_type = 'migraine' THEN 1 END)       AS migraine_events,
    AVG(CASE WHEN event_type = 'migraine' THEN severity END)  AS migraine_avg_severity,
    SUM(CASE WHEN event_type = 'sleep' THEN value_std END)    AS sleep_hours,
    SUM(CASE WHEN event_type = 'stress' THEN value_std END)   AS stress_hours,
    SUM(CASE WHEN event_type = 'meal' THEN value_std END)     AS meals_count
  FROM base
  GROUP BY week_start_monday
)
SELECT
  week_start_monday,
  migraine_events,
  migraine_avg_severity,
  sleep_hours,
  stress_hours,
  meals_count,

  -- previous-week values (lags)
  LAG(migraine_events)         OVER (ORDER BY week_start_monday) AS migraine_events_prev,
  LAG(migraine_avg_severity)   OVER (ORDER BY week_start_monday) AS migraine_severity_prev,
  LAG(sleep_hours)             OVER (ORDER BY week_start_monday) AS sleep_hours_prev,
  LAG(stress_hours)            OVER (ORDER BY week_start_monday) AS stress_hours_prev,
  LAG(meals_count)             OVER (ORDER BY week_start_monday) AS meals_count_prev

FROM weekly
ORDER BY week_start_monday;

  -- 4-week moving averages (including current week)
  AVG(migraine_events)       OVER (ORDER BY week_start_monday ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS ma4_migraine_events,
  AVG(migraine_avg_severity) OVER (ORDER BY week_start_monday ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS ma4_migraine_severity,
  AVG(sleep_hours)           OVER (ORDER BY week_start_monday ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS ma4_sleep_hours,
  AVG(stress_hours)          OVER (ORDER BY week_start_monday ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS ma4_stress_hours,
  AVG(meals_count)           OVER (ORDER BY week_start_monday ROWS BETWEEN 3 PRECEDING AND CURRENT ROW) AS ma4_meals_count


      WITH base AS (
      SELECT
        date(REPLACE(CAST(event_timestamp AS TEXT), 'T', ' '), {modifiers}) AS week_start_monday,
        event_type,
        severity,
        unit,
        numerical_value,
        CASE
          WHEN event_type = 'sleep'  AND unit = 'minutes' THEN numerical_value / 60.0
          WHEN event_type = 'sleep'  AND unit = 'hours'   THEN CAST(numerical_value AS REAL)
          WHEN event_type = 'stress' AND unit = 'minutes' THEN numerical_value / 60.0
          WHEN event_type = 'stress' AND unit = 'hours'   THEN CAST(numerical_value AS REAL)
          WHEN event_type = 'meal'   AND unit = 'number'  THEN CAST(numerical_value AS REAL)
          ELSE NULL
        END AS value_std
      FROM events
  WHERE user_id=replace('4eeebdc1-9e3f-4e0c-86ac-cceb22fc0287', '-', '')
    ),

    -- Aggregate per week (may be sparse)
    weekly_raw AS (
      SELECT
        week_start_monday,
        COUNT(CASE WHEN event_type = 'migraine' THEN 1 END)      AS migraine_events,
        AVG(CASE WHEN event_type = 'migraine' THEN severity END) AS migraine_avg_severity,
        SUM(CASE WHEN event_type = 'sleep'  THEN value_std END)  AS sleep_hours,
        SUM(CASE WHEN event_type = 'stress' THEN value_std END)  AS stress_hours,
        SUM(CASE WHEN event_type = 'meal'   THEN value_std END)  AS meals_count
      FROM base
      GROUP BY week_start_monday
    ),

    -- Bounds from data, optionally overridden by parameters (aligned to Monday)
    limits0 AS (
      SELECT
        MIN(week_start_monday) AS min_week_raw,
        MAX(week_start_monday) AS max_week_raw
      FROM weekly_raw
    ),
    limits AS (
      SELECT
        CASE
          WHEN :start_date IS NOT NULL THEN date(:start_date, 'weekday 1', '-7 days')
          ELSE min_week_raw
        END AS min_week,
        CASE
          WHEN :end_date IS NOT NULL THEN date(:end_date, 'weekday 1', '-7 days')
          ELSE max_week_raw
        END AS max_week
      FROM limits0
    ),

    -- Continuous weekly calendar via recursive CTE
    weeks(week_start_monday) AS (
      SELECT min_week FROM limits
      UNION ALL
      SELECT date(week_start_monday, '+7 days')
      FROM weeks, limits
      WHERE week_start_monday < max_week
    ),

    -- Fill sparse weeks with zeros (for sums/counts); keep NULL for averages
    weekly AS (
      SELECT
        w.week_start_monday,
        COALESCE(wr.migraine_events, 0)      AS migraine_events,
        wr.migraine_avg_severity             AS migraine_avg_severity,
        COALESCE(wr.sleep_hours, 0.0)        AS sleep_hours,
        COALESCE(wr.stress_hours, 0.0)       AS stress_hours,
        COALESCE(wr.meals_count, 0.0)        AS meals_count
      FROM weeks w
      LEFT JOIN weekly_raw wr USING (week_start_monday)
    )

    -- Final: lags, percent changes, and rolling averages
    SELECT
      week_start_monday,
      migraine_events,
      migraine_avg_severity,
      sleep_hours,
      stress_hours,
      meals_count,

      -- Lags
      LAG(migraine_events)       OVER (ORDER BY week_start_monday) AS migraine_events_prev,
      LAG(migraine_avg_severity) OVER (ORDER BY week_start_monday) AS migraine_severity_prev,
      LAG(sleep_hours)           OVER (ORDER BY week_start_monday) AS sleep_hours_prev,
      LAG(stress_hours)          OVER (ORDER BY week_start_monday) AS stress_hours_prev,
      LAG(meals_count)           OVER (ORDER BY week_start_monday) AS meals_count_prev,

      -- Percent changes vs previous week (NULL when prev is NULL or 0)
      CASE
        WHEN LAG(migraine_events) OVER (ORDER BY week_start_monday) IS NULL
          OR LAG(migraine_events) OVER (ORDER BY week_start_monday) = 0
        THEN NULL
        ELSE (migraine_events - LAG(migraine_events) OVER (ORDER BY week_start_monday)) * 1.0
             / LAG(migraine_events) OVER (ORDER BY week_start_monday)
      END AS pct_migraine_events_change,

      CASE
        WHEN LAG(migraine_avg_severity) OVER (ORDER BY week_start_monday) IS NULL
          OR LAG(migraine_avg_severity) OVER (ORDER BY week_start_monday) = 0
        THEN NULL
        ELSE (migraine_avg_severity - LAG(migraine_avg_severity) OVER (ORDER BY week_start_monday)) * 1.0
             / LAG(migraine_avg_severity) OVER (ORDER BY week_start_monday)
      END AS pct_migraine_severity_change,

      CASE
        WHEN LAG(sleep_hours) OVER (ORDER BY week_start_monday) IS NULL
          OR LAG(sleep_hours) OVER (ORDER BY week_start_monday) = 0
        THEN NULL
        ELSE (sleep_hours - LAG(sleep_hours) OVER (ORDER BY week_start_monday)) * 1.0
             / LAG(sleep_hours) OVER (ORDER BY week_start_monday)
      END AS pct_sleep_hours_change,

      CASE
        WHEN LAG(stress_hours) OVER (ORDER BY week_start_monday) IS NULL
          OR LAG(stress_hours) OVER (ORDER BY week_start_monday) = 0
        THEN NULL
        ELSE (stress_hours - LAG(stress_hours) OVER (ORDER BY week_start_monday)) * 1.0
             / LAG(stress_hours) OVER (ORDER BY week_start_monday)
      END AS pct_stress_hours_change,

      CASE
        WHEN LAG(meals_count) OVER (ORDER BY week_start_monday) IS NULL
          OR LAG(meals_count) OVER (ORDER BY week_start_monday) = 0
        THEN NULL
        ELSE (meals_count - LAG(meals_count) OVER (ORDER BY week_start_monday)) * 1.0
             / LAG(meals_count) OVER (ORDER BY week_start_monday)
      END AS pct_meals_count_change,

      -- Rolling averages over `window_size` weeks (including current week)
      AVG(migraine_events)       OVER (ORDER BY week_start_monday ROWS BETWEEN {preceding} PRECEDING AND CURRENT ROW) AS ma_migraine_events,
      AVG(migraine_avg_severity) OVER (ORDER BY week_start_monday ROWS BETWEEN {preceding} PRECEDING AND CURRENT ROW) AS ma_migraine_severity,
      AVG(sleep_hours)           OVER (ORDER BY week_start_monday ROWS BETWEEN {preceding} PRECEDING AND CURRENT ROW) AS ma_sleep_hours,
      AVG(stress_hours)          OVER (ORDER BY week_start_monday ROWS BETWEEN {preceding} PRECEDING AND CURRENT ROW) AS ma_stress_hours,
      AVG(meals_count)           OVER (ORDER BY week_start_monday ROWS BETWEEN {preceding} PRECEDING AND CURRENT ROW) AS ma_meals_count

    FROM weekly
    ORDER BY week_start_monday;

"""

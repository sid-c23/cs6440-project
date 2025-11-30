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

user_id=replace('5456be9d-9bf0-43e5-ac96-512ea8324603', '-', '')

SELECT
  date(REPLACE(event_timestamp, 'T', ' '), 'weekday 1', '-7 days') AS week_start_monday,
  COUNT(*) AS event_count,
  AVG(severity) AS avg_severity
FROM events
WHERE
user_id=replace('5456be9d-9bf0-43e5-ac96-512ea8324603', '-', '')
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
  WHERE user_id=replace('5456be9d-9bf0-43e5-ac96-512ea8324603', '-', '')
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


"""

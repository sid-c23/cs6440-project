from typing import List
from .database import Base
from sqlalchemy import TIMESTAMP, Column, String, Text, Enum, Integer, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy.sql import func
from fastapi_utils.guid_type import GUID, GUID_DEFAULT_SQLITE
import enum

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
    # Data Columns
    severity = Column('severity', Enum(Severity), nullable=True)
    numerical_value = Column(Integer, nullable=True)
    numerical_unit = Column('unit', Enum(Unit), nullable=True)
    description = Column(Text(length=200), nullable=True)
    # Metadata
    creation_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    update_timestamp = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

# End Model definitions

from datetime import datetime
from pydantic import BaseModel
from .models import Event, Severity, Unit

class UserSchema(BaseModel):
    id: str | None = None
    name: str
    creation_timestamp: datetime | None = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbritrary_types_allowed = True

class EventSchema(BaseModel):
    system: str | None = None
    code: str | None = None
    event_type: Event | None = None
    id: str | None = None
    severity: Severity | None = None
    numerical_value: int | None = None
    numerical_unit: Unit | None = None
    description: str | None = None
    creation_timestamp: datetime | None = None
    update_timestamp: datetime | None = None

    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbritrary_types_allowed = True
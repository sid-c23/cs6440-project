from datetime import datetime
from pydantic import BaseModel, Field
from .models import EventType, Severity, Unit

class UserRequest(BaseModel):
    name: str
    class Config:
        orm_mode = True
        allow_population_by_field_name = True
        arbritrary_types_allowed = True

class EventRequest(BaseModel):
    system: str | None = None
    code: str | None = None
    event_type: EventType | None = None
    severity: Severity | None = None
    numerical_value: int | None = None
    numerical_unit: Unit | None = None
    description: str | None = None
    event_timestamp: datetime | None = None
    creation_timestamp: datetime | None = None
    update_timestamp: datetime | None = None

    class Config:
        use_enum_values = True
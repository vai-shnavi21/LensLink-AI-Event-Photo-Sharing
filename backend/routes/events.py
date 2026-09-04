"""Events CRUD router — /events"""
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from routes.auth import current_user
from services import event_service

router = APIRouter(prefix="/events", tags=["Events"])

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class EventCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    event_date: str
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("event_date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not DATE_RE.match(v):
            raise ValueError("event_date must be YYYY-MM-DD")
        return v


class EventUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    event_date: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("event_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not DATE_RE.match(v):
            raise ValueError("event_date must be YYYY-MM-DD")
        return v


@router.post("", status_code=201)
def create_event(data: EventCreate, user=Depends(current_user)):
    try:
        event = event_service.create_event(
            user["id"], data.name, data.event_date, data.description
        )
    except Exception:
        raise HTTPException(500, "Failed to create event")
    return event


@router.get("")
def list_events(user=Depends(current_user)):
    return {"events": event_service.list_events(user["id"])}


@router.get("/{event_id}")
def get_event(event_id: int, user=Depends(current_user)):
    event = event_service.get_event(user["id"], event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return event


@router.put("/{event_id}")
def update_event(event_id: int, data: EventUpdate, user=Depends(current_user)):
    if data.name is None and data.event_date is None and data.description is None:
        raise HTTPException(422, "Provide at least one field to update")
    event = event_service.update_event(
        user["id"], event_id,
        name=data.name,
        event_date=data.event_date,
        description=data.description,
    )
    if not event:
        raise HTTPException(404, "Event not found")
    return event


@router.delete("/{event_id}")
def delete_event(event_id: int, user=Depends(current_user)):
    deleted = event_service.delete_event(user["id"], event_id)
    if not deleted:
        raise HTTPException(404, "Event not found")
    return {"message": "Event deleted"}

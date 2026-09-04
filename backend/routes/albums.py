"""Albums CRUD router — /events/{event_id}/albums"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from routes.auth import current_user
from services import album_service

router = APIRouter(prefix="/events/{event_id}/albums", tags=["Albums"])


class AlbumCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)


class AlbumUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)


@router.post("", status_code=201)
def create_album(event_id: int, data: AlbumCreate, user=Depends(current_user)):
    album = album_service.create_album(user["id"], event_id, data.name, data.description)
    if album is None:
        raise HTTPException(404, "Event not found")
    return album


@router.get("")
def list_albums(event_id: int, user=Depends(current_user)):
    albums = album_service.list_albums(user["id"], event_id)
    if albums is None:
        raise HTTPException(404, "Event not found")
    return {"albums": albums}


@router.put("/{album_id}")
def update_album(event_id: int, album_id: int, data: AlbumUpdate, user=Depends(current_user)):
    if data.name is None and data.description is None:
        raise HTTPException(422, "Provide at least one field to update")
    album = album_service.update_album(user["id"], event_id, album_id, name=data.name, description=data.description)
    if album is None:
        raise HTTPException(404, "Album not found")
    return album


@router.delete("/{album_id}")
def delete_album(event_id: int, album_id: int, user=Depends(current_user)):
    deleted = album_service.delete_album(user["id"], event_id, album_id)
    if not deleted:
        raise HTTPException(404, "Album not found")
    return {"message": "Album deleted"}

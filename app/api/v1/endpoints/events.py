from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Union, Any, Dict, Optional
from app.api import deps
from app.schemas.event import EventCreate, EventUpdate
from app.repositories.event import EventRepository
from bson.errors import InvalidId

router = APIRouter()

@router.post("/", response_model=Any)
async def create_event(
    event_in: Union[EventCreate, List[EventCreate]],
    tenant_id: str = Depends(deps.get_current_tenant_from_api_secret_or_jwt),
    db = Depends(deps.get_mongo_db)
):
    """
    Create a new event logging (treatment).
    Supports either a single event object or an array of event objects.
    """
    repo = EventRepository(db)
    
    if isinstance(event_in, list):
        count = await repo.create_many(tenant_id, event_in)
        return {"status": "ok", "inserted": count}
    else:
        created_event = await repo.create(tenant_id, event_in)
        return {"status": "ok", "inserted": 1, "event": created_event}

@router.get("/", response_model=List[Any])
async def read_events(
    count: int = Query(10, le=1000),
    skip: int = Query(0, ge=0),
    tenant_id: str = Depends(deps.get_current_tenant_from_api_secret_or_jwt),
    db = Depends(deps.get_mongo_db)
):
    """
    Retrieve recent events for the tenant.
    """
    repo = EventRepository(db)
    events = await repo.get_multi_by_tenant(tenant_id, limit=count, skip=skip)
    return events

@router.put("/{event_id}", response_model=Any)
async def update_event(
    event_id: str,
    event_in: EventUpdate,
    tenant_id: str = Depends(deps.get_current_tenant_from_api_secret_or_jwt),
    db = Depends(deps.get_mongo_db)
):
    """
    Update an existing event.
    """
    repo = EventRepository(db)
    updated_event = await repo.update(tenant_id, event_id, event_in)
    
    if not updated_event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return {"status": "ok", "event": updated_event}

@router.delete("/{event_id}")
async def delete_event(
    event_id: str,
    tenant_id: str = Depends(deps.get_current_tenant_from_api_secret_or_jwt),
    db = Depends(deps.get_mongo_db)
):
    """
    Delete an event by ID.
    """
    repo = EventRepository(db)
    success = await repo.delete(tenant_id, event_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Event not found")
        
    return {"status": "ok"}

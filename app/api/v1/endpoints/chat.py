import asyncio
import time
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body, Header, Request, Query, File, UploadFile
from pydantic import BaseModel

from app.api.deps import get_current_tenant_from_api_secret_or_jwt, get_mongo_db
from app.services.ai_agent import AIAgentService
from app.repositories.chat import ChatRepository
from app.repositories.event import EventRepository
from app.schemas.chat import ChatCreate
from app.schemas.event import EventCreate
from app.services.entries import EntriesService

router = APIRouter()

class TextChatRequest(BaseModel):
    message: str
    timezone_offset: int = 0  # In minutes, e.g., -330 for IST (+5:30)

async def fetch_insight_context(db, tenant_id: str, message: str, timezone_offset: int = 0) -> str:
    """Conditionally fetches the last 7 days of data if the user is asking for insights."""
    keywords = ["trend", "insight", "show me", "history", "past", "yesterday", "week", "month", "pattern"]
    if not any(k in message.lower() for k in keywords):
        return ""
        
    now_ms = int(time.time() * 1000)
    seven_days_ago = now_ms - (7 * 24 * 60 * 60 * 1000)
    
    entries_service = EntriesService()
    event_repo = EventRepository(db)
    
    entries_task = entries_service.get_entries_by_timestamp_range(tenant_id=tenant_id, start_ms=seven_days_ago, end_ms=now_ms)
    events_task = event_repo.get_multi_by_tenant(tenant_id=tenant_id, start_date=seven_days_ago, end_date=now_ms, limit=1000)
    
    entries, events = await asyncio.gather(entries_task, events_task)
    
    context = []
    if entries: context.append(f"Recent CGM Readings (sampled): {[e['sgv'] for e in entries[::10]]}")
    if events: context.append(f"Recent Events: {[{'type': ev['eventType'], 'carbs': ev.get('carbs'), 'insulin': ev.get('insulin')} for ev in events]}")
    return " | ".join(context)

@router.post("/text")
async def chat_text(
    payload: TextChatRequest,
    tenant_id: str = Depends(get_current_tenant_from_api_secret_or_jwt),
    db = Depends(get_mongo_db)
):
    """
    Submits a text message to the AI Agent.
    """
    start_time = time.time()
    now_ms = int(start_time * 1000)
    
    historical_context = await fetch_insight_context(db, tenant_id, payload.message, payload.timezone_offset)
    
    loop = asyncio.get_event_loop()
    try:
        bedrock_result = await loop.run_in_executor(
            None, 
            AIAgentService.process_bedrock_chat,
            payload.message,
            now_ms,
            historical_context,
            payload.timezone_offset
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Processing failed: {str(e)}")
        
    extracted_events = bedrock_result.get("extracted_events", [])
    ai_response = bedrock_result.get("ai_response", "I could not generate a response.")
    
    # 2. Insert extracted events
    event_repo = EventRepository(db)
    inserted_event_ids = []
    
    for ev in extracted_events:
        try:
            ev_create = EventCreate(
                tenant_id=tenant_id,
                eventType=ev.get("eventType", "Note"),
                date=ev.get("date", now_ms),
                dateString=ev.get("dateString"),
                carbs=ev.get("carbs"),
                insulin=ev.get("insulin"),
                duration=ev.get("duration"),
                notes=ev.get("notes")
            )
            inserted_id_doc = await event_repo.create(tenant_id, ev_create)
            inserted_id = inserted_id_doc["_id"]
            inserted_event_ids.append(inserted_id)
        except Exception as e:
            print(f"Failed to log extracted event {ev}: {e}")

    # 3. Save the chat transaction to history
    chat_repo = ChatRepository(db)
    chat_log = ChatCreate(
        tenant_id=tenant_id,
        userMessage=payload.message,
        aiResponse=ai_response,
        date=now_ms
    )
    chat_id = await chat_repo.create(chat_log)
    
    return {
        "chat_id": chat_id,
        "ai_response": ai_response,
        "extracted_events": extracted_events,
        "inserted_event_count": len(inserted_event_ids)
    }

@router.get("/history")
async def get_chat_history(
    limit: int = 50,
    skip: int = 0,
    tenant_id: str = Depends(get_current_tenant_from_api_secret_or_jwt),
    db = Depends(get_mongo_db)
):
    chat_repo = ChatRepository(db)
    history = await chat_repo.get_multi_by_tenant(tenant_id=tenant_id, limit=limit, skip=skip)
    return history

from fastapi import UploadFile, File
from app.services.transcribe import TranscribeService

@router.post("/voice")
async def chat_voice(
    file: UploadFile = File(...),
    timezone_offset: int = Query(0),
    tenant_id: str = Depends(get_current_tenant_from_api_secret_or_jwt),
    db = Depends(get_mongo_db)
):
    """
    Submits a voice audio file to the AI Agent.
    1. Transcribes audio to text via AWS Transcribe
    2. Parses events via AI
    3. Saves events and chat log
    """
    start_time = time.time()
    now_ms = int(time.time() * 1000)
    file_bytes = await file.read()
    extension = file.filename.split('.')[-1] if '.' in file.filename else 'mp3'
    
    loop = asyncio.get_event_loop()
    try:
        # Transcribe directly asynchronously via HTTP2
        transcript_text = await TranscribeService.transcribe_audio_file(
            file_bytes,
            extension
        )
        
        if not transcript_text or not transcript_text.strip():
            return {
                "chat_id": None,
                "transcribed_text": "",
                "ai_response": "I couldn't hear anything in that audio. Could you please try speaking again?",
                "extracted_events": [],
                "inserted_event_count": 0
            }

        # Parse & Act
        bedrock_result = await loop.run_in_executor(
            None, 
            AIAgentService.process_bedrock_chat,
            transcript_text,
            now_ms,
            "",
            timezone_offset
        )
    except Exception as e:
        print(f"Voice Processing Error: {e}")
        raise HTTPException(status_code=500, detail=f"Voice Processing failed: {str(e)}")
        
    extracted_events = bedrock_result.get("extracted_events", [])
    ai_response = bedrock_result.get("ai_response", "I could not generate a response.")
    
    # Insert extracted events
    event_repo = EventRepository(db)
    inserted_event_ids = []
    
    for ev in extracted_events:
        try:
            ev_create = EventCreate(
                tenant_id=tenant_id,
                eventType=ev.get("eventType", "Note"),
                date=ev.get("date", now_ms),
                dateString=ev.get("dateString"),
                carbs=ev.get("carbs"),
                insulin=ev.get("insulin"),
                duration=ev.get("duration"),
                notes=ev.get("notes")
            )
            inserted_id_doc = await event_repo.create(tenant_id, ev_create)
            inserted_id = inserted_id_doc["_id"]
            inserted_event_ids.append(inserted_id)
        except Exception as e:
            print(f"Failed to log extracted event {ev}: {e}")

    # Save the chat transaction to history
    chat_repo = ChatRepository(db)
    chat_log = ChatCreate(
        tenant_id=tenant_id,
        userMessage=transcript_text,
        aiResponse=ai_response,
        date=now_ms
    )
    chat_id = await chat_repo.create(chat_log)
    
    return {
        "chat_id": chat_id,
        "transcribed_text": transcript_text,
        "ai_response": ai_response,
        "extracted_events": extracted_events,
        "inserted_event_count": len(inserted_event_ids)
    }


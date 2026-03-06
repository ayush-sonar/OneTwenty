from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import List, Optional, Dict, Any
from app.schemas.event import EventCreate, EventUpdate
import datetime

class EventRepository:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.events
        
    async def create(self, tenant_id: str, event_data: EventCreate) -> Dict[str, Any]:
        doc = event_data.dict(exclude_unset=True)
        doc["tenant_id"] = tenant_id
        
        # Ensure we have a date timestamp for sorting
        if "date" not in doc or doc["date"] is None:
            if "dateString" in doc and doc["dateString"]:
                try:
                    dt = datetime.datetime.fromisoformat(doc["dateString"].replace('Z', '+00:00'))
                    doc["date"] = int(dt.timestamp() * 1000)
                except ValueError:
                    doc["date"] = int(datetime.datetime.utcnow().timestamp() * 1000)
            else:
                doc["date"] = int(datetime.datetime.utcnow().timestamp() * 1000)
                doc["dateString"] = datetime.datetime.utcnow().isoformat() + "Z"
                
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc
        
    async def create_many(self, tenant_id: str, events: List[EventCreate]) -> int:
        docs = []
        for event in events:
            doc = event.dict(exclude_unset=True)
            doc["tenant_id"] = tenant_id
            
            # Ensure timestamp
            if "date" not in doc or doc["date"] is None:
                if "dateString" in doc and doc["dateString"]:
                    try:
                        dt = datetime.datetime.fromisoformat(doc["dateString"].replace('Z', '+00:00'))
                        doc["date"] = int(dt.timestamp() * 1000)
                    except ValueError:
                        doc["date"] = int(datetime.datetime.utcnow().timestamp() * 1000)
                else:
                    doc["date"] = int(datetime.datetime.utcnow().timestamp() * 1000)
                    doc["dateString"] = datetime.datetime.utcnow().isoformat() + "Z"
                    
            docs.append(doc)
            
        if not docs:
            return 0
            
        result = await self.collection.insert_many(docs)
        return len(result.inserted_ids)
        
    async def get_multi_by_tenant(
        self, 
        tenant_id: str, 
        limit: int = 10, 
        skip: int = 0,
        start_date: Optional[int] = None,
        end_date: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        query = {"tenant_id": tenant_id}
        
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query["$gte"] = start_date
            if end_date:
                date_query["$lte"] = end_date
            query["date"] = date_query
            
        cursor = self.collection.find(query).sort("date", -1).skip(skip).limit(limit)
        
        events = []
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            events.append(doc)
            
        return events
        
    async def update(self, tenant_id: str, event_id: str, update_data: EventUpdate) -> Optional[Dict[str, Any]]:
        try:
            obj_id = ObjectId(event_id)
        except Exception:
            return None
            
        update_dict = update_data.dict(exclude_unset=True)
        if not update_dict:
            # Nothing to update, just fetch it
            doc = await self.collection.find_one({"_id": obj_id, "tenant_id": tenant_id})
            if doc:
                doc["_id"] = str(doc["_id"])
            return doc
            
        result = await self.collection.update_one(
            {"_id": obj_id, "tenant_id": tenant_id},
            {"$set": update_dict}
        )
        
        if result.modified_count == 0 and result.matched_count == 0:
            return None
            
        doc = await self.collection.find_one({"_id": obj_id, "tenant_id": tenant_id})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc
        
    async def delete(self, tenant_id: str, event_id: str) -> bool:
        try:
            obj_id = ObjectId(event_id)
        except Exception:
            return False
            
        result = await self.collection.delete_one({"_id": obj_id, "tenant_id": tenant_id})
        return result.deleted_count > 0

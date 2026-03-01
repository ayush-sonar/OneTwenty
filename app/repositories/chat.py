import time
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from app.db.mongo import db
from app.schemas.chat import ChatCreate, ChatInDB

class ChatRepository:
    def __init__(self, datab=None):
        # Allow passing mock db or transaction session, otherwise use global default
        self.db = datab if datab is not None else db.get_db()
        self.collection = self.db["tenant_chats"]

    async def create(self, chat_in: ChatCreate) -> str:
        data = chat_in.dict()
        data["tenant_id"] = str(data["tenant_id"])
        
        now_ms = int(time.time() * 1000)
        if data.get("date") is None:
            data["date"] = now_ms
        if data.get("dateString") is None:
            data["dateString"] = datetime.fromtimestamp(data["date"] / 1000).isoformat() + "Z"
            
        result = await self.collection.insert_one(data)
        return str(result.inserted_id)

    async def get_multi_by_tenant(
        self, tenant_id: str, limit: int = 50, skip: int = 0
    ) -> List[dict]:
        cursor = self.collection.find({"tenant_id": str(tenant_id)})
        cursor.sort("date", -1).skip(skip).limit(limit)
        
        chats = []
        async for document in cursor:
            document["_id"] = str(document["_id"])
            chats.append(document)
            
        return chats

    async def delete(self, id: str, tenant_id: str) -> bool:
        result = await self.collection.delete_one({"_id": ObjectId(id), "tenant_id": str(tenant_id)})
        return result.deleted_count > 0

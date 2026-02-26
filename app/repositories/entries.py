from motor.motor_asyncio import AsyncIOMotorClient
from app.db.mongo import db
from typing import List, Any, Dict

class EntriesRepository:
    def __init__(self):
        # We access the global db instance. In a more advanced setup, inject this.
        pass

    async def create_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        Inserts multiple documents into the 'entries' collection.
        Returns a list of inserted IDs as strings.
        """
        if not documents:
            return []
            
        result = await db.get_db().entries.insert_many(documents)
        return [str(id) for id in result.inserted_ids]

    async def get_many(self, tenant_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches entries for a specific tenant.
        Sorts by date descending (newest first).
        """
        cursor = db.get_db().entries.find({"tenant_id": tenant_id})
        cursor.sort("date", -1).limit(limit)
        
        entries = await cursor.to_list(length=limit)
        
        # Convert ObjectId to string
        for entry in entries:
            entry["_id"] = str(entry["_id"])
            
        return entries

    async def get_by_time_range(self, tenant_id: str, start_time_ms: int, end_time_ms: int) -> List[Dict[str, Any]]:
        """
        Fetches entries for a specific tenant within a time range.
        start_time_ms: Start time in milliseconds (epoch)
        end_time_ms: End time in milliseconds (epoch)
        Sorts by date ascending (oldest first) for chart display.
        """
        import time
        start = time.time()
        
        query = {
            "tenant_id": tenant_id,
            "date": {
                "$gte": start_time_ms,
                "$lte": end_time_ms
            }
        }
        
        print(f"[TIMING] MongoDB query start - tenant: {tenant_id}, range: {start_time_ms} to {end_time_ms}")
        
        cursor = db.get_db().entries.find(query)
        cursor.sort("date", 1)  # Ascending for chart
        
        query_time = time.time()
        print(f"[TIMING] MongoDB query built in {(query_time - start)*1000:.2f}ms")
        
        entries = await cursor.to_list(length=None)
        
        fetch_time = time.time()
        print(f"[TIMING] MongoDB fetch completed in {(fetch_time - query_time)*1000:.2f}ms - {len(entries)} entries")
        
        # Convert ObjectId to string
        for entry in entries:
            entry["_id"] = str(entry["_id"])
        
        total_time = time.time()
        print(f"[TIMING] Total MongoDB operation: {(total_time - start)*1000:.2f}ms")
            
        return entries

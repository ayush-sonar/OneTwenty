from typing import List, Union
from app.repositories.entries import EntriesRepository
from app.schemas.entry import EntryCreate

class EntriesService:
    def __init__(self):
        self.repository = EntriesRepository()

    async def create_entries(self, entries: Union[List[EntryCreate], EntryCreate], tenant_id: str) -> List[str]:
        """
        Processes the input schemas, tags them with the tenant_id,
        and delegates persistence to the repository.
        """
        if not isinstance(entries, list):
            entries = [entries]
            
        documents = []
        for entry in entries:
            doc = entry.dict()
            doc["tenant_id"] = tenant_id
            documents.append(doc)
            
        return await self.repository.create_many(documents)

    async def get_entries(self, tenant_id: str, count: int = 10) -> List[dict]:
        entries = await self.repository.get_many(tenant_id, limit=count)
        
        # Transform to match original Nightscout API format
        for entry in entries:
            if 'date' in entry:
                # Add 'mills' field (duplicate of 'date')
                entry['mills'] = entry['date']
                
                # Add 'utcOffset' (default to 0 for UTC)
                if 'utcOffset' not in entry:
                    entry['utcOffset'] = 0
                
                # Add 'sysTime' (ISO format of date)
                if 'dateString' not in entry:
                    from datetime import datetime
                    entry['dateString'] = datetime.fromtimestamp(entry['date'] / 1000).isoformat() + '.000Z'
                
                # Add 'sysTime' (same as dateString for compatibility)
                entry['sysTime'] = entry.get('dateString')
        
        return entries

    async def get_entries_by_time_range(self, tenant_id: str, hours: int) -> List[dict]:
        """
        Get entries for the last N hours.
        """
        import time
        start = time.time()
        
        from datetime import datetime, timedelta
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Convert to milliseconds
        end_time_ms = int(end_time.timestamp() * 1000)
        start_time_ms = int(start_time.timestamp() * 1000)
        
        calc_time = time.time()
        print(f"[TIMING] Service: Time range calculation took {(calc_time - start)*1000:.2f}ms")
        
        entries = await self.repository.get_by_time_range(tenant_id, start_time_ms, end_time_ms)
        
        repo_time = time.time()
        print(f"[TIMING] Service: Repository call took {(repo_time - calc_time)*1000:.2f}ms")
        
        # Transform to match original Nightscout API format
        for entry in entries:
            if 'date' in entry:
                # Add 'mills' field (duplicate of 'date')
                entry['mills'] = entry['date']
                
                # Add 'utcOffset' (default to 0 for UTC)
                if 'utcOffset' not in entry:
                    entry['utcOffset'] = 0
                
                # Add 'dateString' if not present
                if 'dateString' not in entry:
                    from datetime import datetime
                    entry['dateString'] = datetime.fromtimestamp(entry['date'] / 1000).isoformat() + '.000Z'
                
                # Add 'sysTime' (same as dateString for compatibility)
                entry['sysTime'] = entry.get('dateString')
        
        transform_time = time.time()
        print(f"[TIMING] Service: Data transformation took {(transform_time - repo_time)*1000:.2f}ms")
        print(f"[TIMING] Service: Total service time {(transform_time - start)*1000:.2f}ms")
        
        return entries

    async def get_entries_by_timestamp_range(self, tenant_id: str, start_ms: int, end_ms: int) -> List[dict]:
        """
        Get entries between specific Unix timestamps (in milliseconds).
        """
        import time
        start = time.time()
        
        print(f"[TIMING] Service: Querying range {start_ms} to {end_ms}")
        
        entries = await self.repository.get_by_time_range(tenant_id, start_ms, end_ms)
        
        repo_time = time.time()
        print(f"[TIMING] Service: Repository call took {(repo_time - start)*1000:.2f}ms")
        
        # Transform to match original Nightscout API format
        for entry in entries:
            if 'date' in entry:
                entry['mills'] = entry['date']
                
                if 'utcOffset' not in entry:
                    entry['utcOffset'] = 0
                
                if 'dateString' not in entry:
                    from datetime import datetime
                    entry['dateString'] = datetime.fromtimestamp(entry['date'] / 1000).isoformat() + '.000Z'
                
                entry['sysTime'] = entry.get('dateString')
        
        transform_time = time.time()
        print(f"[TIMING] Service: Data transformation took {(transform_time - repo_time)*1000:.2f}ms")
        print(f"[TIMING] Service: Total service time {(transform_time - start)*1000:.2f}ms")
        
        return entries


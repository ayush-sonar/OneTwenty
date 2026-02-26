from app.db.mongo import db
from bson import ObjectId
from typing import List, Any, Dict


class EntriesRepository:
    def __init__(self):
        pass

    async def upsert_many(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Upserts documents into the 'entries' collection, one at a time.

        Deduplication key: { sysTime, type, tenant_id }
        This mirrors the original Nightscout: entries with the same (sysTime, type)
        are considered identical — retried uploads from xDrip/Loop won't create duplicates.

        Returns the full list of documents as stored (with _id as string).
        """
        if not documents:
            return []

        collection = db.get_db().entries
        result_docs = []

        for doc in documents:
            # Build dedup filter using canonical sysTime + type
            dedup_filter = {
                "sysTime": doc["sysTime"],
                "type": doc.get("type", "sgv"),
                "tenant_id": doc["tenant_id"],
            }

            # Upsert: update if exists (same sysTime+type+tenant), insert if new
            update_result = await collection.update_one(
                dedup_filter,
                {"$set": doc},
                upsert=True
            )

            # Recover the document's _id
            if update_result.upserted_id:
                doc["_id"] = str(update_result.upserted_id)
            else:
                # Was an update — fetch the existing _id
                existing = await collection.find_one(dedup_filter, {"_id": 1})
                if existing:
                    doc["_id"] = str(existing["_id"])

            result_docs.append(doc)

        return result_docs

    async def get_many(self, tenant_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetches entries for a specific tenant.
        Sorts by date descending (newest first).
        """
        cursor = db.get_db().entries.find({"tenant_id": tenant_id})
        cursor.sort("date", -1).limit(limit)

        entries = await cursor.to_list(length=limit)

        for entry in entries:
            entry["_id"] = str(entry["_id"])

        return entries

    async def get_by_time_range(
        self, tenant_id: str, start_time_ms: int, end_time_ms: int
    ) -> List[Dict[str, Any]]:
        """
        Fetches entries for a specific tenant within a time range.
        start_time_ms / end_time_ms: Unix epoch in milliseconds.
        Sorts by date ascending (oldest first — for chart display).
        """
        import time
        t0 = time.time()

        query = {
            "tenant_id": tenant_id,
            "date": {"$gte": start_time_ms, "$lte": end_time_ms},
        }

        print(f"[TIMING] MongoDB query start — tenant: {tenant_id}, range: {start_time_ms} to {end_time_ms}")

        cursor = db.get_db().entries.find(query)
        cursor.sort("date", 1)

        entries = await cursor.to_list(length=None)

        t1 = time.time()
        print(f"[TIMING] MongoDB fetch: {(t1 - t0)*1000:.2f}ms — {len(entries)} entries")

        for entry in entries:
            entry["_id"] = str(entry["_id"])

        return entries

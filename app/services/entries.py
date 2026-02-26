from datetime import datetime, timezone, timedelta
from typing import List, Union
from app.repositories.entries import EntriesRepository
from app.schemas.entry import EntryCreate


def _normalize_entry(doc: dict) -> dict:
    """
    Mirrors original Nightscout's `create()` normalization in lib/server/entries.js.

    For each document:
    1. Parse the client's dateString (with timezone offset) using datetime.fromisoformat,
       or fall back to the `date` epoch milliseconds.
    2. Compute and store:
       - utcOffset  — timezone offset in minutes (same sign convention as JS's getTimezoneOffset, inverted)
       - sysTime    — UTC ISO-8601 string (used as the canonical dedup key)
       - dateString — overwritten to sysTime (normalized UTC ISO)
       - mills      — alias for `date` (unix ms), added for frontend compatibility
    """
    date_str = doc.get("dateString")
    date_ms = doc.get("date")

    parsed = None
    utc_offset_minutes = 0

    if date_str:
        try:
            # fromisoformat handles offsets like +05:30, -07:00, Z (as +00:00)
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            parsed = dt
            if dt.tzinfo is not None:
                utc_offset_minutes = int(dt.utcoffset().total_seconds() / 60)
        except (ValueError, AttributeError):
            pass

    if parsed is None and date_ms is not None:
        # Fallback: treat date as UTC epoch ms
        parsed = datetime.fromtimestamp(date_ms / 1000, tz=timezone.utc)
        utc_offset_minutes = 0

    if parsed is None:
        parsed = datetime.now(tz=timezone.utc)

    # Normalize to UTC
    parsed_utc = parsed.astimezone(timezone.utc)

    # sysTime: canonical UTC ISO string (no microseconds, with Z suffix)
    sys_time = parsed_utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{parsed_utc.microsecond // 1000:03d}Z"

    doc["utcOffset"] = utc_offset_minutes
    doc["sysTime"] = sys_time
    doc["dateString"] = sys_time          # Overwrite to normalized UTC ISO (mirrors original)
    doc["mills"] = doc.get("date", 0)     # Alias expected by frontend

    # Ensure type defaults to "sgv"
    if "type" not in doc or not doc["type"]:
        doc["type"] = "sgv"

    return doc


def _strip_internal_fields(entry: dict) -> dict:
    """Remove fields that are internal implementation details and should not be in API responses."""
    entry.pop("tenant_id", None)
    return entry


class EntriesService:
    def __init__(self):
        self.repository = EntriesRepository()

    async def create_entries(
        self, entries: Union[List[EntryCreate], EntryCreate], tenant_id: str
    ) -> List[dict]:
        """
        Normalizes incoming entries (date fields, sysTime, utcOffset),
        tags them with tenant_id, then upserts via repository.

        Returns the full list of stored documents (with _id).
        """
        if not isinstance(entries, list):
            entries = [entries]

        documents = []
        for entry in entries:
            doc = entry.dict()
            doc["tenant_id"] = tenant_id
            doc = _normalize_entry(doc)
            documents.append(doc)

        stored = await self.repository.upsert_many(documents)

        # Strip tenant_id from response — it's an internal field
        return [_strip_internal_fields(dict(d)) for d in stored]

    async def get_entries(self, tenant_id: str, count: int = 10) -> List[dict]:
        entries = await self.repository.get_many(tenant_id, limit=count)
        return [_strip_internal_fields(e) for e in entries]

    async def get_entries_by_time_range(self, tenant_id: str, hours: int) -> List[dict]:
        """
        Get entries for the last N hours.
        """
        import time
        t0 = time.time()

        end_dt = datetime.now(tz=timezone.utc)
        start_dt = end_dt - timedelta(hours=hours)

        end_ms = int(end_dt.timestamp() * 1000)
        start_ms = int(start_dt.timestamp() * 1000)

        print(f"[TIMING] Service: Time range calc {(time.time() - t0)*1000:.2f}ms")

        entries = await self.repository.get_by_time_range(tenant_id, start_ms, end_ms)

        print(f"[TIMING] Service: Repo call {(time.time() - t0)*1000:.2f}ms")

        return [_strip_internal_fields(e) for e in entries]

    async def get_entries_by_timestamp_range(
        self, tenant_id: str, start_ms: int, end_ms: int
    ) -> List[dict]:
        """
        Get entries between specific Unix timestamps (milliseconds).
        """
        import time
        t0 = time.time()

        print(f"[TIMING] Service: Querying range {start_ms} to {end_ms}")

        entries = await self.repository.get_by_time_range(tenant_id, start_ms, end_ms)

        print(f"[TIMING] Service: Repo call {(time.time() - t0)*1000:.2f}ms")

        return [_strip_internal_fields(e) for e in entries]

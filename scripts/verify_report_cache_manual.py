import asyncio
import os
import sys
import datetime

# Ensure app is in path
sys.path.append(os.getcwd())

from app.api.v1.endpoints.reports import generate_report
from app.db.mongo import db

async def verify_report_cache():
    # 1. Initialize MongoDB
    db.connect()
    mongo_db = db.get_db()
    
    tenant_id = "test_tenant_cache"
    report_range = "1d"
    s3_key = "reports/tester_dummy.pdf"
    
    try:
        # Pre-cleanup
        await mongo_db.reports.delete_many({"tenant_id": tenant_id})

        # 2. Insert a dummy report generated "today"
        print(f"Step 1: Inserting dummy report for tenant '{tenant_id}'...")
        await mongo_db.reports.insert_one({
            "tenant_id": tenant_id,
            "range": report_range,
            "report_url": "https://dummy-url.com/expires",
            "s3_key": s3_key,
            "created_at": datetime.datetime.utcnow(),
            "expires_in": 3600
        })

        # 3. Call generate_report - Should be cached immediately
        print("Step 2: Calling generate_report (should be cached)...")
        # NOTE: We can't easily avoid the dependency imports, but we can see if it reaches the cache check
        result = await generate_report(range=report_range, tenant_id=tenant_id, db=mongo_db)
        
        print(f"Result: cached={result.get('cached')}, s3_key_preserved={s3_key in result['report_url']}")
        
        if result.get("cached") is True:
            print("\nReport caching (retrieval logic) SUCCESS")
        else:
            print("\nFAILED: Cache was not hit.")
            
    except Exception as e:
        print(f"Verification failed with error: {str(e)}")
        # import traceback
        # traceback.print_exc()
    finally:
        await mongo_db.reports.delete_many({"tenant_id": tenant_id})
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_report_cache())

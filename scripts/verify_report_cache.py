import asyncio
import os
import sys

# Ensure app is in path
sys.path.append(os.getcwd())

from app.api.v1.endpoints.reports import generate_report
from app.db.mongo import db
from unittest.mock import MagicMock, AsyncMock

async def verify_report_cache():
    # 1. Initialize MongoDB
    db.connect()
    mongo_db = db.get_db()
    
    tenant_id = "1"
    
    try:
        # 2. Call generate_report - First Time (Should generate)
        print("Step 1: Calling generate_report for 1d (First time)...")
        result1 = await generate_report(range="1d", tenant_id=tenant_id, db=mongo_db)
        print(f"Result 1: cached={result1.get('cached')}, url_len={len(result1['report_url'])}")
        
        # 3. Call generate_report - Second Time (Should be cached)
        print("\nStep 2: Calling generate_report for 1d (Second time)...")
        result2 = await generate_report(range="1d", tenant_id=tenant_id, db=mongo_db)
        print(f"Result 2: cached={result2.get('cached')}, url_len={len(result2['report_url'])}")
        
        # Verify results
        if result1["cached"] is not False:
            print("FAILED: First call should NOT be cached.")
        elif result2["cached"] is not True:
            print("FAILED: Second call SHOULD be cached.")
        elif result1["report_url"] == result2["report_url"]:
             print("FAILED: URLs should be different (freshly signed).")
        else:
            print("\nReport caching verification SUCCESS")
            
    except Exception as e:
        print(f"Verification failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(verify_report_cache())

from fastapi import APIRouter, Depends, Request, Header, HTTPException
from typing import Optional
from app.api.deps import get_tenant_from_jwt, get_tenant_from_api_key
from app.repositories.tenant import TenantRepository

router = APIRouter()

@router.get("/status")
@router.get("/status.json")
async def get_status(
    api_secret: Optional[str] = Header(None, alias="api-secret"),
    request: Request = None
):
    """
    Returns the Nightscout status/configuration for the authenticated user's tenant.
    This replaces the environment-variable-based configuration in the original Nightscout.
    
    The frontend uses this endpoint to initialize itself.
    """
    tenant_id = None

    # 1. Try API key first (for Nightscout uploaders)
    if api_secret:
        # Standard behavior: if key is invalid, 401. 
        # But we'll let dependency handle exception if we call it directly
        tenant_id = get_tenant_from_api_key(request, api_secret)

    # 2. If no API key, check Authorization header (JWT)
    if not tenant_id:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                from jose import jwt
                from app.core.config import settings
                from app.repositories.user import UserRepository
                
                token = auth_header.replace("Bearer ", "")
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
                user_id = int(payload.get("sub"))
                
                repo = UserRepository()
                tenant_id = repo.get_tenant_for_user(user_id)
                if tenant_id:
                    tenant_id = str(tenant_id)
            except Exception as e:
                pass # Invalid JWT, fall through
        
    # 3. If still no tenant, try Subdomain (Public Read-Only)
    if not tenant_id:
        from app.api.deps import get_tenant_from_subdomain
        tenant_id = get_tenant_from_subdomain(request)
        
    if not tenant_id:
         raise HTTPException(status_code=401, detail="Authentication required (API Key, JWT, or valid Subdomain)")

    repo = TenantRepository()
    tenant_info = repo.get_tenant_info(int(tenant_id))
    
    if not tenant_info:
        return {"status": "error", "message": "Tenant not found"}
    
    settings = tenant_info.get("settings", {})
    
    # Build the status response in the format the Nightscout client expects
    return {
        "status": "ok",
        "name": tenant_info.get("name", "Nightscout"),
        "version": "15.0.0-saas",  # Custom version identifier
        "serverTime": None,  # Will be filled by middleware if needed
        "apiEnabled": True,
        "careportalEnabled": True,
        "boluscalcEnabled": True,
        "settings": settings,
        "extendedSettings": {
            "devicestatus": {
                "advanced": True
            }
        },
        # These are critical for the UI to render correctly
        "units": settings.get("units", "mg/dl"),
        "enable": settings.get("enable", []),
        "thresholds": {
            "bg_high": settings.get("alarm_high", 180),
            "bg_target_top": settings.get("bg_target_top", 180),
            "bg_target_bottom": settings.get("bg_target_bottom", 80),
            "bg_low": settings.get("alarm_low", 70)
        }
    }

@router.put("/settings")
async def update_settings(
    settings_update: dict,
    tenant_id: str = Depends(get_tenant_from_jwt)
):
    """
    Update tenant settings.
    Accepts partial updates - only provided fields will be updated.
    """
    from app.core.logging import logger
    
    repo = TenantRepository()
    
    # Get current settings
    current_settings = repo.get_settings(int(tenant_id))
    
    # Merge with updates
    updated_settings = {**current_settings, **settings_update}
    
    # Save updated settings
    repo.update_settings(int(tenant_id), updated_settings)
    
    logger.info(
        "Tenant settings updated",
        extra={
            'extra_data': {
                'tenant_id': tenant_id,
                'updated_fields': list(settings_update.keys())
            }
        }
    )
    
    return {
        "status": "ok",
        "message": "Settings updated successfully",
        "settings": updated_settings
    }

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.clock import ClockConfigResponse, ClockConfigCreate, ClockConfigUpdate, ClockAssignment
from app.repositories.clock import ClockRepository
from typing import Optional

router = APIRouter()

@router.get("/clock-config", response_model=ClockConfigResponse)
async def get_clock_config(clock_id: str, repo: ClockRepository = Depends()):
    """
    Fetch clock configuration by clock_id.
    """
    config = repo.get_by_clock_id(clock_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for clock '{clock_id}' not found"
        )
    return config

@router.post("/clock-config", response_model=ClockConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_clock_config(config_in: ClockConfigCreate, repo: ClockRepository = Depends()):
    """
    Create a new clock configuration.
    """
    existing = repo.get_by_clock_id(config_in.clock_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Configuration for clock '{config_in.clock_id}' already exists. Use PUT to update."
        )
    return repo.create(
        clock_id=config_in.clock_id,
        wifi_name=config_in.wifi_name,
        wifi_password=config_in.wifi_password,
        user_subdomain_url=config_in.user_subdomain_url
    )

@router.put("/clock-config", response_model=ClockConfigResponse)
async def update_clock_config(config_in: ClockConfigCreate, repo: ClockRepository = Depends()):
    """
    Update an existing clock configuration (upsert-like behavior if desired, but here we require existence).
    """
    existing = repo.get_by_clock_id(config_in.clock_id)
    if not existing:
        # Alternatively, we could create it here if we want PUT to be idempotent create/update
        return repo.create(
            clock_id=config_in.clock_id,
            wifi_name=config_in.wifi_name,
            wifi_password=config_in.wifi_password,
            user_subdomain_url=config_in.user_subdomain_url
        )
    
    return repo.update(
        clock_id=config_in.clock_id,
        wifi_name=config_in.wifi_name,
        wifi_password=config_in.wifi_password,
        user_subdomain_url=config_in.user_subdomain_url
    )

@router.post("/assign-clock", response_model=ClockConfigResponse)
async def assign_clock(assignment: ClockAssignment, repo: ClockRepository = Depends()):
    """
    Assign a clock to a user subdomain.
    """
    config = repo.assign_to_subdomain(
        clock_id=assignment.clock_id,
        user_subdomain_url=assignment.user_subdomain_url
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clock '{assignment.clock_id}' not found"
        )
    return config

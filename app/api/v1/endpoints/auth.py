from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.auth import UserCreate, UserLogin, Token
from app.services.auth import AuthService
from app.core import security
from jose import jwt, JWTError
from app.core.config import settings
from fastapi.security import OAuth2PasswordBearer

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        return int(user_id)
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

@router.post("/signup", response_model=dict)
def signup(user_in: UserCreate):
    service = AuthService()
    user = service.signup(user_in)
    return {"message": "User created successfully", "user_id": user["public_id"]}

@router.post("/login", response_model=Token)
def login(login_in: UserLogin):
    service = AuthService()
    return service.login(login_in)
    
@router.post("/refresh-token", response_model=Token)
def refresh_token(refresh_token: str):
    # Simplified refresh flow (verify signature + issue new pair)
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
             raise HTTPException(status_code=400, detail="Invalid token type")
        
        user_id = payload.get("sub")
        new_access = security.create_access_token(subject=user_id)
        return Token(
            access_token=new_access, 
            refresh_token=refresh_token, # Keep same refresh or rotate? Keeping same for MVP
            token_type="bearer"
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

@router.post("/api-secret")
def get_api_secret(user_id: int = Depends(get_current_user_id)):
    """
    Returns the existing API secret for the user's tenant, or creates one if none exists.
    Authenticated via JWT.
    """
    service = AuthService()
    secret = service.get_or_create_api_key(user_id)
    return {"api_secret": secret}

@router.post("/reset-api-secret")
def reset_api_secret(user_id: int = Depends(get_current_user_id)):
    """
    Revokes the old API Secret and generates a NEW one.
    Authenticated via JWT.
    """
    service = AuthService()
    new_secret = service.rotate_api_key(user_id)
    return {"api_secret": new_secret}

@router.get("/profile")
def get_profile(user_id: int = Depends(get_current_user_id)):
    """
    Returns the current user's profile including their tenant slug for subdomain URL.
    """
    from app.repositories.user import UserRepository
    import psycopg2
    from app.db.session import get_db_connection
    
    user_repo = UserRepository()
    
    # Get tenant ID for user
    tenant_id = user_repo.get_tenant_for_user(user_id)
    if not tenant_id:
        raise HTTPException(status_code=404, detail="User has no tenant")
    
    # Get tenant slug directly from database
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT slug, name FROM tenants WHERE id = %s", (tenant_id,))
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tenant not found")
            
            slug, name = row
            return {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "tenant_name": name,
                "slug": slug,
                "subdomain_url": f"https://{slug}.onetwenty.dev"
            }
    finally:
        conn.close()

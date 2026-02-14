from typing import Any, Dict, Optional
from fastapi import HTTPException, status
from app.repositories.user import UserRepository
from app.core import security
from app.schemas.auth import UserCreate, UserLogin, Token, TokenData

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def signup(self, user_in: UserCreate) -> Dict[str, Any]:
        """
        Registers a new user + tenant.
        """
        existing_user = self.user_repo.get_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        hashed_password = security.get_password_hash(user_in.password)
        user = self.user_repo.create(email=user_in.email, hashed_password=hashed_password)
        return user

    def login(self, login_in: UserLogin) -> Token:
        """
        Authenticates a user via email (as user_id) or public_id?
        The prompt said "only take user_id and password". 
        I will assume user_id typically means email.
        """
        user = self.user_repo.get_by_email(login_in.user_id)
        if not user or not security.verify_password(login_in.password, user["hashed_password"]):
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token = security.create_access_token(subject=user["id"])
        refresh_token = security.create_refresh_token(subject=user["id"])
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
        
    def get_or_create_api_key(self, user_id: int) -> str:
        # Get user's primary tenant
        tenant_id = self.user_repo.get_tenant_for_user(user_id)
        if not tenant_id:
             raise HTTPException(status_code=404, detail="User has no tenant")
        
        # Check for existing key
        existing_key = self.user_repo.get_active_api_key(tenant_id)
        if existing_key:
            return existing_key

        return self.user_repo.create_api_key(tenant_id)

    def rotate_api_key(self, user_id: int) -> str:
        tenant_id = self.user_repo.get_tenant_for_user(user_id)
        if not tenant_id:
             raise HTTPException(status_code=404, detail="User has no tenant")
        
        # Revoke all existing keys
        self.user_repo.revoke_api_keys(tenant_id)
        
        # Create new one
        return self.user_repo.create_api_key(tenant_id, description="Rotated Key")

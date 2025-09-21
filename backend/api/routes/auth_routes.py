"""
Authentication Routes for Perfect21 Claude Enhancer
Provides JWT-based authentication endpoints
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter()
security = HTTPBearer()

# Request/Response models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    created_at: datetime
    is_active: bool

# Mock user database (replace with actual database)
MOCK_USERS = {
    "admin@claude-enhancer.com": {
        "id": "user_001",
        "email": "admin@claude-enhancer.com",
        "full_name": "Claude Administrator",
        "password_hash": "$2b$12$mock_hash_for_development",
        "created_at": datetime.utcnow(),
        "is_active": True
    }
}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user information"""

    token = credentials.credentials

    # Mock token verification (replace with actual JWT verification)
    if token == "mock_valid_token":
        return {
            "user_id": "user_001",
            "email": "admin@claude-enhancer.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

async def get_current_user(token_data: Dict[str, Any] = Depends(verify_token)) -> UserResponse:
    """Get current authenticated user"""

    user_id = token_data.get("user_id")
    email = token_data.get("email")

    # Mock user lookup (replace with actual database query)
    user_data = MOCK_USERS.get(email)

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(**user_data)

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate user and return JWT tokens"""

    logger.info("Login attempt", email=request.email)

    # Mock authentication (replace with actual password verification)
    user = MOCK_USERS.get(request.email)

    if not user or request.password != "admin123":  # Mock password check
        logger.warning("Failed login attempt", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Mock token generation (replace with actual JWT generation)
    logger.info("Successful login", email=request.email, user_id=user["id"])

    return TokenResponse(
        access_token="mock_valid_token",
        refresh_token="mock_refresh_token",
        expires_in=3600
    )

@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest) -> UserResponse:
    """Register a new user"""

    logger.info("Registration attempt", email=request.email)

    # Check if user already exists
    if request.email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )

    # Mock user creation (replace with actual database insertion)
    user_data = {
        "id": f"user_{len(MOCK_USERS) + 1:03d}",
        "email": request.email,
        "full_name": request.full_name,
        "password_hash": "$2b$12$mock_hash_for_development",
        "created_at": datetime.utcnow(),
        "is_active": True
    }

    MOCK_USERS[request.email] = user_data

    logger.info("User registered successfully", email=request.email, user_id=user_data["id"])

    return UserResponse(**user_data)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str) -> TokenResponse:
    """Refresh access token using refresh token"""

    # Mock token refresh (replace with actual JWT refresh logic)
    if refresh_token != "mock_refresh_token":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    return TokenResponse(
        access_token="mock_valid_token_refreshed",
        refresh_token="mock_refresh_token",
        expires_in=3600
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Get current user information"""

    return current_user

@router.post("/logout")
async def logout(current_user: UserResponse = Depends(get_current_user)) -> Dict[str, str]:
    """Logout user (invalidate token)"""

    logger.info("User logged out", user_id=current_user.id, email=current_user.email)

    # In a real implementation, you would invalidate the token
    # by adding it to a blacklist or removing it from Redis

    return {"message": "Successfully logged out"}

@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: UserResponse = Depends(get_current_user)
) -> Dict[str, str]:
    """Change user password"""

    logger.info("Password change attempt", user_id=current_user.id)

    # Mock password verification (replace with actual password verification)
    if current_password != "admin123":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Mock password update (replace with actual password hashing and database update)
    logger.info("Password changed successfully", user_id=current_user.id)

    return {"message": "Password changed successfully"}
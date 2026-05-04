"""Auth API routes with complete JWT authentication and sample data."""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr, field_validator
import secrets
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings
from app.models.schemas.user import Token, LoginRequest, UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService
from app.services.examples import SampleDataService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    include_samples: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **username**: Username for login (3-100 chars, must be unique)
    - **password**: Password (min 6 characters)
    - **full_name**: Optional display name
    - **include_samples**: Whether to create sample data (default: true)
    """
    user_service = UserService(db)
    
    # Check if email already exists
    if await user_service.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if await user_service.username_exists(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    try:
        user = await user_service.create(user_data)
        
        # Create sample data for new user
        if include_samples:
            try:
                sample_service = SampleDataService(db)
                await sample_service.initialize_user_samples(user.id)
            except Exception as e:
                # Log but don't fail registration if sample creation fails
                from loguru import logger
                logger.warning(f"Failed to create sample data for user {user.id}: {e}")
        
        await db.commit()
        return UserResponse.model_validate(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User creation failed - please try again"
        )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    Login with username/email and password.
    
    Returns JWT access token on success.
    Use the token in Authorization header: `Bearer <token>`
    """
    user_service = UserService(db)
    user = await user_service.authenticate(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user info
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "email": user.email
        }
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/json", response_model=Token)
async def login_json(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with JSON body (alternative to form-based login).
    
    - **username**: Email or username
    - **password**: Password
    """
    user_service = UserService(db)
    user = await user_service.authenticate(login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "email": user.email
        }
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's information.
    
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile.
    
    Only updates fields that are provided (partial update).
    To change password, include 'password' field.
    """
    user_service = UserService(db)
    
    # Check email uniqueness if being changed
    if user_data.email and user_data.email != current_user.email:
        if await user_service.email_exists(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    # Check username uniqueness if being changed
    if user_data.username and user_data.username != current_user.username:
        if await user_service.username_exists(user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    updated_user = await user_service.update(current_user.id, user_data)
    return UserResponse.model_validate(updated_user)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token for current user.
    
    Issues a new JWT token with the same user identity.
    """
    access_token = create_access_token(
        data={
            "sub": current_user.username,
            "user_id": current_user.id,
            "email": current_user.email
        }
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout current user.
    
    Note: JWT tokens are stateless, so this endpoint mainly serves
    as a client-side signal. For true logout, the client should
    discard the token.
    """
    return {"message": "Successfully logged out"}


@router.get("/onboarding")
async def get_onboarding_data(
    current_user: User = Depends(get_current_user)
):
    """
    Get onboarding checklist and welcome message for new users.
    """
    from app.services.examples.sample_data import ONBOARDING_CHECKLIST, WELCOME_MESSAGE
    
    # Check if user has any existing data
    from sqlalchemy import select, func
    from app.models.conversation import Conversation
    from app.models.knowledge import KnowledgeBase
    from app.models.workflow import Workflow
    
    # Count user's resources
    conv_count = await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user.id)
    )
    kb_count = await db.execute(
        select(func.count()).select_from(KnowledgeBase).where(KnowledgeBase.user_id == current_user.id)
    )
    wf_count = await db.execute(
        select(func.count()).select_from(Workflow).where(Workflow.user_id == current_user.id)
    )
    
    has_data = conv_count.scalar() > 0 or kb_count.scalar() > 0 or wf_count.scalar() > 0
    
    return {
        "welcome_message": WELCOME_MESSAGE,
        "checklist": ONBOARDING_CHECKLIST,
        "is_new_user": not has_data,
    }


@router.post("/init-samples")
async def initialize_sample_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize sample data for current user.
    Creates example knowledge bases, workflows, and conversations.
    """
    from sqlalchemy import select, func
    from app.models.conversation import Conversation
    
    # Check if user already has data
    conv_count = await db.execute(
        select(func.count()).select_from(Conversation).where(Conversation.user_id == current_user.id)
    )
    
    if conv_count.scalar() > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sample data already exists for this user"
        )
    
    sample_service = SampleDataService(db)
    result = await sample_service.initialize_user_samples(current_user.id)
    await db.commit()
    
    return {
        "message": "Sample data created successfully",
        **result
    }


# ============================================
# P0: Password Reset / Forgot Password
# ============================================

class ForgotPasswordRequest(BaseModel):
    """Request model for forgot password."""
    email: EmailStr
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return v.lower().strip()


class ResetPasswordRequest(BaseModel):
    """Request model for password reset."""
    token: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class ChangePasswordRequest(BaseModel):
    """Request model for changing password (authenticated)."""
    current_password: str
    new_password: str
    
    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


# In-memory token storage (in production, use Redis or database)
_password_reset_tokens: dict = {}


def _generate_reset_token(email: str) -> str:
    """Generate a secure reset token."""
    token = secrets.token_urlsafe(32)
    _password_reset_tokens[token] = {
        'email': email.lower(),
        'created_at': datetime.utcnow(),
        'expires_at': datetime.utcnow() + timedelta(hours=1)
    }
    return token


def _verify_reset_token(token: str) -> str | None:
    """Verify a reset token and return the email if valid."""
    token_data = _password_reset_tokens.get(token)
    if not token_data:
        return None
    
    if datetime.utcnow() > token_data['expires_at']:
        del _password_reset_tokens[token]
        return None
    
    return token_data['email']


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request a password reset link.
    
    Sends a password reset email to the user if the email exists.
    Always returns success to prevent email enumeration attacks.
    """
    user_service = UserService(db)
    user = await user_service.get_by_email(request.email)
    
    if user:
        # Generate reset token
        token = _generate_reset_token(request.email)
        
        # In production, send email here
        # For now, we'll log the token (remove in production)
        from loguru import logger
        reset_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/auth/reset-password?token={token}"
        logger.info(f"Password reset link for {request.email}: {reset_url}")
        
        # TODO: Send actual email via configured email service
        # Example with SMTP or email service like SendGrid:
        # await send_password_reset_email(request.email, reset_url)
    
    # Always return success to prevent email enumeration
    return {
        "message": "If an account with that email exists, a password reset link has been sent."
    }


@router.post("/reset-password")
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using a valid token.
    
    - **token**: The reset token from the email link
    - **new_password**: The new password (min 6 characters)
    """
    email = _verify_reset_token(request.token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user_service = UserService(db)
    user = await user_service.get_by_email(email)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    await db.commit()
    
    # Remove used token
    del _password_reset_tokens[request.token]
    
    return {"message": "Password has been reset successfully"}


@router.post("/change-password", response_model=UserResponse)
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password for authenticated user.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (min 6 characters)
    """
    user_service = UserService(db)
    
    # Verify current password
    user = await user_service.authenticate(current_user.username, request.current_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Update to new password
    user.hashed_password = get_password_hash(request.new_password)
    await db.commit()
    
    return UserResponse.model_validate(user)

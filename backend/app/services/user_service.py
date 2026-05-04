"""User service for database operations."""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.user import User
from app.models.schemas.user import UserCreate, UserUpdate, UserResponse
from app.core.security import get_password_hash, verify_password


class UserService:
    """Service for user-related database operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            id=str(uuid.uuid4()),
            email=user_data.email,
            username=user_data.username,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def update(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        
        update_data = user_data.model_dump(exclude_unset=True)
        
        # Handle password update
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(user)
        
        return user
    
    async def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password."""
        user = await self.get_by_username(username)
        if not user:
            # Try email
            user = await self.get_by_email(username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        # Update last login
        user.last_login = datetime.utcnow()
        await self.db.flush()
        
        return user
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.db.flush()
    
    async def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False
    ) -> tuple[List[User], int]:
        """List users with pagination."""
        query = select(User)
        
        if not include_inactive:
            query = query.where(User.is_active == True)
        
        # Count total
        count_result = await self.db.execute(
            select(User.id).where(User.is_active == True) if not include_inactive else select(User.id)
        )
        total = len(count_result.all())
        
        # Get paginated results
        query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def delete(self, user_id: str) -> bool:
        """Soft delete user (set is_active=False)."""
        user = await self.get_by_id(user_id)
        if not user:
            return False
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        await self.db.flush()
        
        return True
    
    async def email_exists(self, email: str) -> bool:
        """Check if email already exists."""
        result = await self.db.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
    
    async def username_exists(self, username: str) -> bool:
        """Check if username already exists."""
        result = await self.db.execute(
            select(User.id).where(User.username == username)
        )
        return result.scalar_one_or_none() is not None

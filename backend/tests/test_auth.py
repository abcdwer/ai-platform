"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient


class TestAuthRegister:
    """Test user registration endpoint."""
    
    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepassword123",
                "full_name": "New User",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Test registration with existing email fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": test_user.email,  # Already exists
                "username": "differentuser",
                "password": "password123",
            },
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Test registration with existing username fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,  # Already exists
                "password": "password123",
            },
        )
        
        assert response.status_code == 400
        assert "Username already taken" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email fails."""
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "validuser",
                "password": "password123",
            },
        )
        
        assert response.status_code == 422  # Validation error


class TestAuthLogin:
    """Test user login endpoint."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "testpassword123",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password fails."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": test_user.username,
                "password": "wrongpassword",
            },
        )
        
        assert response.status_code == 401
        assert "Incorrect username/email or password" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with nonexistent user fails."""
        response = await client.post(
            "/api/auth/login",
            data={
                "username": "nonexistent",
                "password": "password123",
            },
        )
        
        assert response.status_code == 401


class TestAuthMe:
    """Test current user endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_authenticated(self, authenticated_client: AsyncClient, test_user):
        """Test getting current user info when authenticated."""
        response = await authenticated_client.get("/api/auth/me")
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email
    
    @pytest.mark.asyncio
    async def test_get_current_user_unauthenticated(self, client: AsyncClient):
        """Test getting current user info without authentication fails."""
        response = await client.get("/api/auth/me")
        
        assert response.status_code == 401


class TestAuthPassword:
    """Test password update endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_password_success(self, authenticated_client: AsyncClient):
        """Test successful password update."""
        response = await authenticated_client.put(
            "/api/auth/password",
            json={
                "current_password": "testpassword123",
                "new_password": "newpassword456",
            },
        )
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password updated successfully"
    
    @pytest.mark.asyncio
    async def test_update_password_wrong_current(self, authenticated_client: AsyncClient):
        """Test password update with wrong current password fails."""
        response = await authenticated_client.put(
            "/api/auth/password",
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword456",
            },
        )
        
        assert response.status_code == 400
        assert "Current password is incorrect" in response.json()["detail"]

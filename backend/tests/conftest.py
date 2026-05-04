"""Pytest configuration and fixtures for backend tests."""
import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Set test environment
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"

from app.main import create_app
from app.core.database import Base, get_db
from app.core.security import create_access_token, get_password_hash

# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for tests."""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture(scope="function")
async def app(db_session: AsyncSession) -> AsyncGenerator:
    """Create test application."""
    application = create_app()
    
    # Override database dependency
    async def override_get_db():
        yield db_session
    
    application.dependency_overrides[get_db] = override_get_db
    
    yield application
    
    application.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    from app.models.user import User
    import uuid
    
    user = User(
        id=str(uuid.uuid4()),
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
def auth_headers(test_user) -> dict:
    """Create authentication headers with valid JWT token."""
    token = create_access_token(
        data={
            "sub": test_user.username,
            "user_id": test_user.id,
            "email": test_user.email,
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, auth_headers: dict) -> AsyncClient:
    """Create authenticated test client."""
    client.headers.update(auth_headers)
    return client


@pytest_asyncio.fixture
async def test_conversation(db_session: AsyncSession, test_user):
    """Create a test conversation."""
    from app.models.conversation import Conversation
    
    conversation = Conversation(
        id="test-conv-001",
        user_id=test_user.id,
        title="Test Conversation",
        model="llama2",
        model_provider="ollama",
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest_asyncio.fixture
async def test_knowledge_base(db_session: AsyncSession, test_user):
    """Create a test knowledge base."""
    from app.models.knowledge import KnowledgeBase
    
    kb = KnowledgeBase(
        id="test-kb-001",
        user_id=test_user.id,
        name="Test Knowledge Base",
        description="A test knowledge base",
    )
    db_session.add(kb)
    await db_session.commit()
    await db_session.refresh(kb)
    return kb


@pytest_asyncio.fixture
async def test_workflow(db_session: AsyncSession, test_user):
    """Create a test workflow."""
    from app.models.workflow import Workflow, WorkflowStatus
    
    workflow = Workflow(
        id="test-wf-001",
        user_id=test_user.id,
        name="Test Workflow",
        description="A test workflow",
        status=WorkflowStatus.DRAFT.value,
        graph_data={"nodes": [], "edges": []},
    )
    db_session.add(workflow)
    await db_session.commit()
    await db_session.refresh(workflow)
    return workflow

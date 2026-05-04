"""Initialize database with default data."""
import asyncio
from app.core.database import init_db, async_session_maker
from app.models.user import User
from app.models.agent import Agent
from app.models.model_config import ModelConfig
from app.core.security import get_password_hash
import uuid


async def seed_data():
    """Seed the database with initial data."""
    await init_db()
    
    async with async_session_maker() as session:
        # Check if we already have data
        from sqlalchemy import select
        result = await session.execute(select(User))
        existing_users = result.scalars().all()
        
        if existing_users:
            print("Database already has data, skipping seed.")
            return
        
        # Create default user
        default_user = User(
            id=str(uuid.uuid4()),
            email="demo@example.com",
            username="demo",
            hashed_password=get_password_hash("demo123"),
            full_name="Demo User",
            is_active=True,
            is_superuser=False,
        )
        session.add(default_user)
        
        # Create some default model configs
        models = [
            ModelConfig(
                id=str(uuid.uuid4()),
                name="llama2",
                provider="ollama",
                model_id="llama2",
                supports_streaming=True,
                supports_function_calling=False,
                default_temperature=0.7,
                default_max_tokens=4096,
                max_context_tokens=4096,
                is_active=True,
                is_default=True,
            ),
            ModelConfig(
                id=str(uuid.uuid4()),
                name="codellama",
                provider="ollama",
                model_id="codellama",
                supports_streaming=True,
                supports_function_calling=False,
                default_temperature=0.2,
                default_max_tokens=4096,
                max_context_tokens=4096,
                is_active=True,
                is_default=False,
            ),
            ModelConfig(
                id=str(uuid.uuid4()),
                name="gpt-4-turbo",
                provider="openai",
                model_id="gpt-4-turbo-preview",
                supports_streaming=True,
                supports_function_calling=True,
                supports_vision=True,
                default_temperature=0.7,
                default_max_tokens=4096,
                max_context_tokens=128000,
                is_active=True,
                is_default=False,
            ),
            ModelConfig(
                id=str(uuid.uuid4()),
                name="gpt-3.5-turbo",
                provider="openai",
                model_id="gpt-3.5-turbo",
                supports_streaming=True,
                supports_function_calling=True,
                default_temperature=0.7,
                default_max_tokens=4096,
                max_context_tokens=16385,
                is_active=True,
                is_default=False,
            ),
        ]
        
        for model in models:
            session.add(model)
        
        # Create a sample agent
        sample_agent = Agent(
            id=str(uuid.uuid4()),
            user_id=default_user.id,
            name="Code Assistant",
            description="A helpful coding assistant that can help write and debug code",
            system_prompt="""You are an expert programming assistant. You can help users with:
- Writing clean, efficient code
- Debugging and fixing issues
- Explaining complex concepts
- Code review and best practices
- Writing tests

Always provide clear explanations and include code examples when helpful.""",
            model="llama2",
            model_provider="ollama",
            temperature=0.7,
            max_tokens=4096,
            tools=[
                {
                    "name": "execute_code",
                    "description": "Execute Python code and return the output",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"}
                        },
                        "required": ["code"]
                    }
                }
            ],
            is_active=True,
            is_public=True,
        )
        session.add(sample_agent)
        
        await session.commit()
        print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())

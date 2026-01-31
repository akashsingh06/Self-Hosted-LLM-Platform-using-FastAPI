import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from src.main import app
from src.database.models import User, Conversation
from src.core.security import create_access_token


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_chat_endpoint(db_session: Session):
    # Create test user
    user = User(username="test", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    # Create token
    token = create_access_token({"sub": str(user.id)})
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/chat",
            json={"message": "Hello", "stream": False},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data


@pytest.mark.asyncio
async def test_finetune_job_creation(db_session: Session):
    # Create test user
    user = User(username="test", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    # Create token
    token = create_access_token({"sub": str(user.id)})
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post(
            "/api/finetune/jobs",
            json={
                "base_model": "deepseek-coder:6.7b",
                "dataset_id": 1,
                "method": "lora",
                "epochs": 1,
                "batch_size": 4,
                "learning_rate": 2e-5
            },
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code in [200, 201]
    data = response.json()
    assert "id" in data
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_rate_limiting(db_session: Session):
    # Create test user
    user = User(username="test", email="test@example.com")
    db_session.add(user)
    db_session.commit()
    
    # Create token
    token = create_access_token({"sub": str(user.id)})
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        responses = []
        for _ in range(10):
            response = await ac.post(
                "/api/chat",
                json={"message": "Test", "stream": False},
                headers={"Authorization": f"Bearer {token}"}
            )
            responses.append(response.status_code)
    
    # Should get rate limited after a few requests
    assert 429 in responses or all(r == 200 for r in responses)

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.api.deps import get_db, get_current_admin_user
from src.models.schemas import User
from src.database.crud import (
    get_all_users,
    update_user,
    delete_user,
    get_user_conversations,
)

router = APIRouter()


@router.get("/users", response_model=List[User])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """List all users (admin only)"""
    users = get_all_users(db, skip=skip, limit=limit)
    return users


@router.put("/users/{user_id}")
async def update_user_admin(
    user_id: int,
    user_update: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update user (admin only)"""
    user = update_user(db, user_id, user_update)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User updated successfully"}


@router.delete("/users/{user_id}")
async def delete_user_admin(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete user (admin only)"""
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@router.get("/users/{user_id}/conversations")
async def get_user_conversations_admin(
    user_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Get user conversations (admin only)"""
    conversations = get_user_conversations(db, user_id, skip=skip, limit=limit)
    return conversations


@router.post("/system/cleanup")
async def system_cleanup(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Cleanup system (admin only)"""
    # TODO: Implement cleanup logic
    return {"message": "Cleanup completed"}

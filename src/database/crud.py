from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta

from .models import (
    User, Conversation, Message, FinetuneJob, 
    FinetuneDataset, CodeBlock, SystemLog
)


# User CRUD
def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_data: dict) -> User:
    user = User(**user_data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def update_user(db: Session, user_id: int, user_data: dict) -> Optional[User]:
    user = get_user_by_id(db, user_id)
    if user:
        for key, value in user_data.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
    return user

def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False

def get_all_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    return db.query(User).offset(skip).limit(limit).all()


# Conversation CRUD
def create_conversation(db: Session, **kwargs) -> Conversation:
    conversation = Conversation(**kwargs)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

def get_conversation(db: Session, conversation_id: int, user_id: Optional[int] = None) -> Optional[Conversation]:
    query = db.query(Conversation).filter(Conversation.id == conversation_id)
    if user_id:
        query = query.filter(Conversation.user_id == user_id)
    return query.first()

def get_user_conversations(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[Conversation]:
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == user_id)
        .order_by(desc(Conversation.updated_at))
        .offset(skip)
        .limit(limit)
        .all()
    )

def update_conversation(db: Session, conversation_id: int, update_data: dict) -> Optional[Conversation]:
    conversation = get_conversation(db, conversation_id)
    if conversation:
        for key, value in update_data.items():
            setattr(conversation, key, value)
        db.commit()
        db.refresh(conversation)
    return conversation

def delete_conversation(db: Session, conversation_id: int, user_id: Optional[int] = None) -> bool:
    conversation = get_conversation(db, conversation_id, user_id)
    if conversation:
        db.delete(conversation)
        db.commit()
        return True
    return False


# Message CRUD
def add_message(db: Session, **kwargs) -> Message:
    message = Message(**kwargs)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_conversation_messages(db: Session, conversation_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .offset(skip)
        .limit(limit)
        .all()
    )


# Finetune Job CRUD
def create_finetune_job(db: Session, job_data: dict) -> FinetuneJob:
    job = FinetuneJob(**job_data)
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_finetune_job(db: Session, job_id: int) -> Optional[FinetuneJob]:
    return db.query(FinetuneJob).filter(FinetuneJob.id == job_id).first()

def list_finetune_jobs(db: Session, user_id: Optional[int] = None, limit: int = 50, offset: int = 0) -> List[FinetuneJob]:
    query = db.query(FinetuneJob)
    if user_id:
        query = query.filter(FinetuneJob.user_id == user_id)
    return query.order_by(desc(FinetuneJob.created_at)).offset(offset).limit(limit).all()

def update_finetune_job(db: Session, job_id: int, update_data: dict) -> Optional[FinetuneJob]:
    job = get_finetune_job(db, job_id)
    if job:
        for key, value in update_data.items():
            setattr(job, key, value)
        db.commit()
        db.refresh(job)
    return job


# Code Block CRUD
def save_code_block(db: Session, code_data: dict) -> CodeBlock:
    code_block = CodeBlock(**code_data)
    db.add(code_block)
    db.commit()
    db.refresh(code_block)
    return code_block

def get_code_blocks_by_message(db: Session, message_id: int) -> List[CodeBlock]:
    return db.query(CodeBlock).filter(CodeBlock.message_id == message_id).all()


# System Log CRUD
def create_system_log(db: Session, log_data: dict) -> SystemLog:
    log = SystemLog(**log_data)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def get_system_logs(db: Session, level: Optional[str] = None, limit: int = 100) -> List[SystemLog]:
    query = db.query(SystemLog)
    if level:
        query = query.filter(SystemLog.level == level)
    return query.order_by(desc(SystemLog.created_at)).limit(limit).all()


# Cleanup functions
def cleanup_expired_data(db: Session, days: int = 30):
    """Cleanup old data"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Delete old system logs
    db.query(SystemLog).filter(SystemLog.created_at < cutoff_date).delete()
    
    # Delete conversations without messages older than cutoff
    db.query(Conversation).filter(
        and_(
            Conversation.created_at < cutoff_date,
            ~Conversation.messages.any()
        )
    ).delete()
    
    db.commit()

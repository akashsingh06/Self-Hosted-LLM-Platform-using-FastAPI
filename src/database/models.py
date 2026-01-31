from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, 
    ForeignKey, JSON, Float, BigInteger
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

from src.database.session import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    finetune_jobs = relationship("FinetuneJob", back_populates="user")


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    model_name = Column(String(100), nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    # Computed columns (not stored, for convenience)
    @property
    def message_count(self):
        return len(self.messages)
    
    @property
    def token_count(self):
        return sum(m.tokens or 0 for m in self.messages)


class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    tokens = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class FinetuneJob(Base):
    __tablename__ = "finetune_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    base_model = Column(String(100), nullable=False)
    new_model_name = Column(String(100), nullable=True)
    dataset_path = Column(String(500), nullable=False)
    method = Column(String(50), nullable=False)  # lora, p_tuning, prefix_tuning, full
    status = Column(String(20), default="pending")  # pending, running, completed, failed, cancelled
    epochs = Column(Integer, default=5)
    batch_size = Column(Integer, default=4)
    learning_rate = Column(Float, default=2e-5)
    lora_rank = Column(Integer, nullable=True)
    target_modules = Column(JSON, nullable=True)  # List of module names
    loss_history = Column(JSON, nullable=True)  # List of loss values
    metrics = Column(JSON, nullable=True)  # Training metrics
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="finetune_jobs")


class FinetuneDataset(Base):
    __tablename__ = "finetune_datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    format = Column(String(20), nullable=False)  # jsonl, csv, parquet
    file_path = Column(String(500), nullable=False)
    size = Column(BigInteger, default=0)  # File size in bytes
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    user = relationship("User")


class CodeBlock(Base):
    __tablename__ = "code_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    language = Column(String(50), nullable=True)
    code = Column(Text, nullable=False)
    start_line = Column(Integer, nullable=False)
    end_line = Column(Integer, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    message = relationship("Message")


class SystemLog(Base):
    __tablename__ = "system_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False)  # INFO, WARNING, ERROR, DEBUG
    module = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)


class CacheEntry(Base):
    __tablename__ = "cache_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    ttl = Column(Integer, nullable=False)  # Time to live in seconds
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

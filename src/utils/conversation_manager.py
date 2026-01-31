import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from loguru import logger

from src.config.settings import settings


@dataclass
class ConversationMessage:
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    tokens: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationManager:
    """Manage conversations with file-based persistence"""
    
    def __init__(self, storage_path: str = "./data/conversations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.conversations: Dict[str, 'Conversation'] = {}
    
    def create_conversation(self, title: str, model: str) -> str:
        """Create a new conversation"""
        from uuid import uuid4
        conv_id = str(uuid4())
        
        conversation = Conversation(
            id=conv_id,
            title=title,
            model=model,
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )
        
        self.conversations[conv_id] = conversation
        self._save_conversation(conversation)
        
        return conv_id
    
    def add_message(self, conv_id: str, role: str, content: str, tokens: Optional[int] = None) -> bool:
        """Add message to conversation"""
        if conv_id not in self.conversations:
            return False
        
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            tokens=tokens,
        )
        
        self.conversations[conv_id].messages.append(message)
        self.conversations[conv_id].updated_at = datetime.now().isoformat()
        
        self._save_conversation(self.conversations[conv_id])
        return True
    
    def get_conversation(self, conv_id: str) -> Optional['Conversation']:
        """Get conversation by ID"""
        if conv_id in self.conversations:
            return self.conversations[conv_id]
        
        # Try to load from file
        file_path = self.storage_path / f"{conv_id}.json"
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                conversation = Conversation.from_dict(data)
                self.conversations[conv_id] = conversation
                return conversation
            except Exception as e:
                logger.error(f"Error loading conversation {conv_id}: {e}")
        
        return None
    
    def list_conversations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List all conversations"""
        conversations = []
        
        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                conversations.append({
                    'id': data['id'],
                    'title': data['title'],
                    'model': data['model'],
                    'created_at': data['created_at'],
                    'updated_at': data['updated_at'],
                    'message_count': len(data['messages']),
                })
            except Exception as e:
                logger.error(f"Error reading conversation file {file_path}: {e}")
        
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x['updated_at'], reverse=True)
        return conversations[:limit]
    
    def delete_conversation(self, conv_id: str) -> bool:
        """Delete conversation"""
        if conv_id in self.conversations:
            del self.conversations[conv_id]
        
        file_path = self.storage_path / f"{conv_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        
        return False
    
    def _save_conversation(self, conversation: 'Conversation'):
        """Save conversation to file"""
        file_path = self.storage_path / f"{conversation.id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(conversation), f, indent=2, ensure_ascii=False)


@dataclass
class Conversation:
    """Conversation data class"""
    id: str
    title: str
    model: str
    messages: List[ConversationMessage]
    created_at: str
    updated_at: str
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Conversation':
        """Create Conversation from dict"""
        messages = [
            ConversationMessage(**msg) if isinstance(msg, dict) else msg
            for msg in data.get('messages', [])
        ]
        
        return cls(
            id=data['id'],
            title=data['title'],
            model=data['model'],
            messages=messages,
            created_at=data['created_at'],
            updated_at=data['updated_at'],
        )
    
    def to_dict(self) -> dict:
        """Convert to dict"""
        return {
            'id': self.id,
            'title': self.title,
            'model': self.model,
            'messages': [asdict(msg) for msg in self.messages],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }

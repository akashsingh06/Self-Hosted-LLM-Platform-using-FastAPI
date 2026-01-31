from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import json

from src.api.deps import get_db, get_current_user
from src.models.schemas import ChatRequest, ChatResponse, User
from src.services.llm_service import LLMService
from src.database.crud import (
    create_conversation,
    add_message,
    get_conversation,
)
from src.utils.code_extractor import CodeExtractor

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(lambda: router.llm_service),
):
    """Chat with LLM"""
    try:
        # Get or create conversation
        conversation = None
        if request.conversation_id:
            conversation = get_conversation(db, request.conversation_id, current_user.id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = create_conversation(
                db,
                user_id=current_user.id,
                title=request.message[:50],
                model_name=request.model_name or "default",
            )
        
        # Add user message
        user_msg = add_message(
            db,
            conversation_id=conversation.id,
            role="user",
            content=request.message,
        )
        
        # Build conversation history
        history = "\n".join([
            f"{'Human' if m.role == 'user' else 'Assistant'}: {m.content}"
            for m in conversation.messages[-10:]  # Last 10 messages for context
        ])
        
        prompt = f"{history}\n\nHuman: {request.message}\nAssistant:"
        
        # Get response from LLM
        full_response = ""
        async for chunk in llm_service.generate(
            prompt=prompt,
            model=request.model_name,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=False,
        ):
            full_response += chunk
        
        # Add assistant message
        assistant_msg = add_message(
            db,
            conversation_id=conversation.id,
            role="assistant",
            content=full_response,
        )
        
        # Extract code blocks
        code_extractor = CodeExtractor()
        code_blocks = code_extractor.extract_blocks(full_response)
        
        # TODO: Save code blocks to database
        
        return ChatResponse(
            message=full_response,
            conversation_id=conversation.id,
            message_id=assistant_msg.id,
            tokens_used=len(full_response.split()),  # Approximate
            processing_time=0.0,  # TODO: Track actual time
            code_blocks=[block.dict() for block in code_blocks],
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    llm_service: LLMService = Depends(lambda: router.llm_service),
):
    """Chat with streaming response"""
    
    async def event_generator():
        try:
            # Build prompt (simplified for streaming)
            prompt = f"Human: {request.message}\nAssistant:"
            
            # Stream response
            async for chunk in llm_service.generate(
                prompt=prompt,
                model=request.model_name,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            ):
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
            
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
        }
    )

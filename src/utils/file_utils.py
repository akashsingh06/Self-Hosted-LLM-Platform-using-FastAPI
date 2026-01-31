import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional, Set
from datetime import datetime
import aiofiles
from fastapi import UploadFile
from loguru import logger

from src.config.settings import settings


async def save_upload_file(
    upload_file: UploadFile,
    prefix: str = "uploads",
    allowed_extensions: Optional[Set[str]] = None
) -> Path:
    """Save uploaded file with safety checks"""
    
    # Create upload directory
    upload_dir = Path(settings.UPLOAD_PATH) / prefix
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate safe filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = upload_file.filename or "file"
    file_ext = Path(original_filename).suffix.lower()
    
    # Check extension
    if allowed_extensions and file_ext not in allowed_extensions:
        raise ValueError(f"File extension {file_ext} not allowed")
    
    # Create unique filename
    file_hash = hashlib.md5(f"{timestamp}_{original_filename}".encode()).hexdigest()[:8]
    safe_filename = f"{timestamp}_{file_hash}{file_ext}"
    file_path = upload_dir / safe_filename
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await upload_file.read()
            await f.write(content)
        
        logger.info(f"File saved: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        if file_path.exists():
            file_path.unlink()
        raise


def get_export_path(filename: str) -> Path:
    """Get export file path"""
    export_dir = Path(settings.EXPORT_PATH)
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Add timestamp to avoid collisions
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = filename.replace(" ", "_").replace("/", "_")
    return export_dir / f"{timestamp}_{safe_name}"


def cleanup_old_files(directory: Path, max_age_days: int = 7):
    """Cleanup old files in directory"""
    if not directory.exists():
        return
    
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)
    
    for file_path in directory.iterdir():
        if file_path.is_file():
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")


def get_directory_size(directory: Path) -> int:
    """Get total size of directory in bytes"""
    if not directory.exists():
        return 0
    
    total_size = 0
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
    
    return total_size


def get_file_info(file_path: Path) -> dict:
    """Get file information"""
    if not file_path.exists():
        return {}
    
    stat = file_path.stat()
    return {
        "path": str(file_path),
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "extension": file_path.suffix.lower(),
        "filename": file_path.name,
    }

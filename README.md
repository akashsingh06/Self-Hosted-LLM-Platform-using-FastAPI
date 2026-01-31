
# Enterprise Local LLM Platform

A production-ready platform for running, fine-tuning, and managing local LLMs with enterprise features.

## Features

- **Multi-Model Support**: Run multiple LLM models simultaneously
- **Load Balancing**: Distribute requests across multiple Ollama instances
- **Fine-Tuning Interface**: GUI and API for fine-tuning models (LoRA, P-Tuning, etc.)
- **Redis Caching**: Intelligent response caching
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Conversation Management**: Persistent chat history
- **Code Export**: Automatic extraction and export of code blocks
- **Multi-User Support**: User authentication and authorization
- **Rate Limiting**: Protect against abuse
- **Streaming Responses**: Real-time token streaming
- **Docker Support**: Easy deployment with Docker Compose

## Quick Start
### Run the fix script:
-python fix_ollama.py

### use the quick start:
python quick_start.py

### Test everything:
python test_ollama.py

### Prerequisites

- Docker and Docker Compose
- Python 3.9+
- Ollama (for local development)

### Development Setup

1. **Clone and install:**
```bash
git clone <repository>
cd local-llm-platform
make install




** Restart Ollama to clear any stuck processes:**
Open a NEW PowerShell window and run:

powershell
# Stop Ollama if running
Get-Process -Name "ollama" | Stop-Process -Force

# Wait a moment
Start-Sleep -Seconds 3

# Start Ollama fresh
ollama serve

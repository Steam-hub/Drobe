# Audio Chat API - Child Learning Assistant

A Django-based streaming audio chat API powered by **Gemini Live API** with **native audio streaming**, designed to help children aged 4-10 with game challenges through interactive, real-time voice conversations.

## Features

- **Gemini Live API Integration**: Native bidirectional audio streaming (NEW)
- **Child-Friendly AI Assistant**: Age-appropriate responses tailored for children aged 4-10
- **Real-Time Audio Streaming**: WebSocket-based audio chat for live conversations with true voice
- **Conversation History**: Full context maintained across sessions
- **Visual Assistance**: Upload screenshots for image-based help
- **No Authentication Required**: Simple, frictionless experience (admin panel requires auth)
- **RESTful API**: Clean REST endpoints for session management

## Technology Stack

- **Backend**: Django 4.2+, Django REST Framework
- **Real-Time**: Django Channels, WebSocket
- **AI**: Google Gemini Live API (`gemini-2.5-flash-native-audio-preview-09-2025`)
- **SDK**: NEW `google-genai` package (requires Python 3.9+)
- **Database**: SQLite (development), supports PostgreSQL/MySQL
- **Image Processing**: Pillow
- **Audio**: Native PCM streaming (16kHz input, 24kHz output)

## Quick Start

### Option 1: Docker Deployment (Recommended for Production)

**Prerequisites:**
- Docker & Docker Compose
- AWS Account (for S3 file storage)
- Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

See **[QUICKSTART.md](QUICKSTART.md)** for complete Docker deployment guide.

**Quick Deploy:**
```bash
# 1. Clone and configure
git clone <repo-url>
cd Drobe
cp .env.example .env
# Edit .env with your credentials

# 2. Deploy all services with one command
docker-compose up -d

# 3. Create admin user
docker-compose exec web python manage.py createsuperuser
```

Your app will be running with:
- **Nginx** (reverse proxy on port 80)
- **Django + uWSGI** (HTTP requests)
- **Daphne** (WebSocket connections)
- **PostgreSQL** (database)
- **Redis** (channel layers)
- **S3** (file storage)

### Option 2: Local Development

**Prerequisites:**
- **Python 3.9+** (REQUIRED for Gemini Live API)
- pip
- Virtual environment (recommended)
- Gemini API Key from [Google AI Studio](https://aistudio.google.com/app/apikey)

**IMPORTANT:** The Gemini Live API requires the NEW `google-genai` SDK, which only works with Python 3.9 or higher.

### 2. Installation

```bash
# Verify Python version (MUST be 3.9+)
python --version

# Clone the repository
cd Drobe

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install NEW Gemini SDK (requires Python 3.9+)
pip install google-genai

# Install other dependencies
pip install django==4.2.7 djangorestframework django-cors-headers channels daphne pillow python-dotenv websockets

# Create .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

**For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md)**

### 3. Configuration

Edit `.env` file:
```env
GEMINI_API_KEY=your-api-key-here
SECRET_KEY=your-secret-key
DEBUG=True
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### 6. Start the Server

For development with Channels support:
```bash
daphne -b 0.0.0.0 -p 8000 Drobe.asgi:application
```

Or using Django's development server (REST API only):
```bash
python manage.py runserver
```

### 7. Access the Application

- **API Base URL**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/
- **Health Check**: http://localhost:8000/api/health/
- **WebSocket**: ws://localhost:8000/ws/audio-chat/{session_id}/

## API Endpoints

### REST API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health/` | GET | Health check |
| `/api/sessions/` | GET | List active sessions |
| `/api/sessions/` | POST | Create new session |
| `/api/sessions/{id}/` | GET | Get session details |
| `/api/sessions/{id}/end_session/` | POST | End session |
| `/api/screenshot/` | POST | Upload screenshot |
| `/api/history/` | GET | Get chat history |

### WebSocket

**URL Pattern**: `ws://localhost:8000/ws/audio-chat/{session_id}/`

**Text Message Format**:
```json
{
    "type": "text",
    "content": "I need help with the puzzle!"
}
```

**Audio Message Format** (Binary or Base64):
```javascript
// Option 1: Send as binary (recommended)
ws.send(audioBytesBlob);  // 16-bit PCM, 16kHz, mono

// Option 2: Send as base64 in JSON
{
    "type": "audio_base64",
    "content": "base64_encoded_audio_data"
}
```

**Response Formats**:

*Text Response:*
```json
{
    "type": "response",
    "content": "Sure! Let me help you with that...",
    "session_id": "uuid"
}
```

*Audio Response (Binary):*
```javascript
// Received as binary blob (24kHz PCM mono)
ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // Audio data from Gemini Live API
        playAudio(event.data);
    }
}
```

**Audio Format Requirements:**
- **Input**: 16-bit PCM, 16kHz, mono
- **Output**: 16-bit PCM, 24kHz, mono

## Postman Collection

Import `Audio_Chat_API.postman_collection.json` into Postman to test all endpoints.

The collection includes:
- Health check
- Create/manage chat sessions
- Upload screenshots
- Retrieve chat history
- WebSocket connection info

## Usage Example

### 1. Create a Chat Session

```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "level_description": "Level 3: Collect 5 stars by jumping over obstacles",
    "child_age": 7
  }'
```

Response:
```json
{
    "id": "uuid-here",
    "level_description": "Level 3: Collect 5 stars by jumping over obstacles",
    "child_age": 7,
    "created_at": "2025-01-15T10:30:00Z",
    "is_active": true
}
```

### 2. Connect to WebSocket

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/audio-chat/uuid-here/');

ws.onopen = () => {
    console.log('Connected to Gemini Live API!');
    // Send text message
    ws.send(JSON.stringify({
        type: 'text',
        content: 'I need help with this level!'
    }));
};

ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // Binary audio response (24kHz PCM)
        console.log('Received audio:', event.data);
        playAudio(event.data);
    } else {
        // Text response
        const data = JSON.parse(event.data);
        console.log('AI Response:', data.content);
    }
};

// Send audio data (16kHz PCM mono)
function sendAudio(audioBlob) {
    ws.send(audioBlob);
}
```

### 3. Upload Screenshot

```bash
curl -X POST http://localhost:8000/api/screenshot/ \
  -F "session_id=uuid-here" \
  -F "image=@screenshot.png" \
  -F "question=What should I do here?"
```

## Project Structure

```
Drobe/
├── audio_chat/              # Main app
│   ├── models.py            # ChatSession, ChatMessage
│   ├── views.py             # REST API views
│   ├── serializers.py       # DRF serializers
│   ├── consumers.py         # WebSocket consumer (NEW - uses Live API)
│   ├── routing.py           # WebSocket routing
│   ├── urls.py              # REST URL routing
│   ├── admin.py             # Admin configuration
│   └── services/
│       └── gemini_live_service.py # NEW google-genai SDK integration
├── Drobe/                   # Project settings
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL routing
│   └── asgi.py              # ASGI configuration
├── manage.py
├── .env.example             # Environment variables template
├── README.md                # This file
├── INSTALLATION.md          # Detailed installation guide
├── CHAT_HISTORY_IMPLEMENTATION.md  # Chat history docs
├── GEMINI_LIVE_API_UPGRADE_GUIDE.md # Live API upgrade guide
└── Audio_Chat_API.postman_collection.json
```

## Child-Friendly AI Behavior

The AI assistant is configured to:
- Use simple, age-appropriate language
- Be patient, positive, and encouraging
- Provide gentle hints rather than direct answers
- Celebrate effort and progress
- Make learning fun and engaging
- Adjust tone based on child's age (4-10)

## Development Notes

### Channel Layers

Currently using `InMemoryChannelLayer` for development. For production, use Redis:

```python
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

### Production Considerations

1. Set `DEBUG=False`
2. Configure `ALLOWED_HOSTS`
3. Use PostgreSQL/MySQL
4. Set up Redis for channel layers
5. Configure CORS properly
6. Use a production ASGI server (Daphne/Uvicorn)
7. Set up proper logging
8. Implement rate limiting
9. **Use Docker deployment** (see [QUICKSTART.md](QUICKSTART.md))
10. **Configure S3 for file storage** (see [S3_SETUP.md](S3_SETUP.md))

### AWS S3 File Storage

All files uploaded through Django Admin automatically save to AWS S3 bucket: `file-upload-lambda-bucket-2025`

**Setup:**
1. See [S3_SETUP.md](S3_SETUP.md) for complete S3 configuration
2. Set `USE_S3=True` in `.env`
3. Add AWS credentials to `.env`

**Configuration:**
```env
USE_S3=True
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=file-upload-lambda-bucket-2025
AWS_S3_REGION_NAME=us-east-1
```

### Docker Deployment Guides

- **[QUICKSTART.md](QUICKSTART.md)** - Fast EC2 deployment
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment with SSL
- **[S3_SETUP.md](S3_SETUP.md)** - AWS S3 configuration

## Troubleshooting

### Python Version Error

**Error:** `google-genai requires Python 3.9+`

**Solution:** Upgrade to Python 3.9 or higher. See [INSTALLATION.md](INSTALLATION.md) for detailed instructions.

### WebSocket Connection Issues

- Ensure you're using `daphne` server or `python manage.py runserver` (with Channels configured)
- Check that channels is properly installed
- Verify ASGI configuration in `asgi.py`

### Gemini Live API Errors

**Error:** `No module named 'google.genai'`

**Solution:** Install the NEW SDK: `pip install google-genai`

**Error:** `Live API connection failed`

**Solution:**
- Verify your API key in `.env`
- Check API quotas at [Google AI Studio](https://aistudio.google.com/)
- Ensure you have the latest `google-genai` package
- Verify network connectivity

### Audio Format Issues

**Error:** Audio not playing or distorted

**Solution:**
- Ensure input audio is 16-bit PCM, 16kHz, mono
- Output audio from Gemini is 24kHz PCM mono
- Check client-side audio playback implementation

### Media Files Not Uploading

- Check `MEDIA_ROOT` and `MEDIA_URL` in settings
- Ensure the `media/` directory exists and is writable
- Verify file size limits (max 5MB for images)

For more troubleshooting, see [INSTALLATION.md](INSTALLATION.md)

## Support

For issues and questions:
- Check the API documentation in Postman collection
- Review Django and Channels documentation
- Check Gemini API documentation

## License

[Add your license here]

## Credits

Built with:
- Django & Django REST Framework
- Django Channels
- Google Gemini AI
- And lots of love for helping kids learn!

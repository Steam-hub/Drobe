# Installation Guide - Audio Chat API with Gemini Live

## Overview

This project uses **Gemini Live API** with **native audio streaming** for real-time bidirectional voice conversations between children (ages 4-10) and an AI assistant.

## Requirements

### Critical Requirement: Python 3.9+

The Gemini Live API requires the **NEW `google-genai` SDK**, which only works with **Python 3.9 or higher**.

```bash
# Check your Python version
python --version

# Must show: Python 3.9.x or higher (3.10, 3.11, 3.12, etc.)
```

**If you have Python 3.8 or lower, you MUST upgrade before proceeding.**

---

## Step 1: Upgrade Python (If Needed)

### Windows

1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. Run the installer
3. **IMPORTANT**: Check "Add Python to PATH"
4. Verify installation:
   ```bash
   python --version
   ```

### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev

# Set as default (optional)
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Verify
python3 --version
```

### macOS

```bash
# Using Homebrew
brew install python@3.11

# Verify
python3 --version
```

---

## Step 2: Create Virtual Environment

```bash
# Navigate to project directory
cd C:\Users\OSAMA\SteamHubGame\Drobe

# Create virtual environment with Python 3.9+
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
source venv/bin/activate

# Verify Python version in virtual environment
python --version
```

---

## Step 3: Install Dependencies

### Install NEW Gemini SDK

```bash
# IMPORTANT: This is the NEW SDK (requires Python 3.9+)
pip install google-genai
```

### Install Other Dependencies

```bash
# Django and REST Framework
pip install django==4.2.7
pip install djangorestframework
pip install django-cors-headers

# Django Channels for WebSocket
pip install channels
pip install daphne

# Other dependencies
pip install pillow
pip install python-dotenv
pip install websockets
```

### Or Install All at Once

```bash
pip install django==4.2.7 djangorestframework django-cors-headers channels daphne pillow python-dotenv websockets google-genai
```

---

## Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Create .env file
touch .env
```

Add the following to `.env`:

```env
# Gemini API Key (REQUIRED)
GEMINI_API_KEY=your_gemini_api_key_here

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Get your Gemini API Key:**
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Copy and paste into `.env`

---

## Step 5: Run Database Migrations

```bash
# Apply migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser for admin panel
python manage.py createsuperuser
```

---

## Step 6: Test Installation

### Test 1: Verify Python Version

```bash
python --version
# Should show 3.9.x or higher
```

### Test 2: Verify NEW SDK Installation

```bash
python -c "from google import genai; print('✅ google-genai SDK installed correctly')"
```

If you see an error like `ModuleNotFoundError: No module named 'google.genai'`, you need to:
- Ensure Python 3.9+
- Install google-genai: `pip install google-genai`

### Test 3: Verify Live API Connection

Create a test file `test_live_api.py`:

```python
import asyncio
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()

async def test_live_api():
    client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

    config = {
        "response_modalities": ["AUDIO"],
        "speech_config": {
            "voice_config": {
                "prebuilt_voice_config": {
                    "voice_name": "Charon"
                }
            }
        }
    }

    try:
        async with client.aio.live.connect(
            model="gemini-2.5-flash-native-audio-preview-09-2025",
            config=config
        ) as session:
            print("✅ Successfully connected to Gemini Live API!")

            # Send test text
            await session.send(
                input="Hello, can you hear me?",
                end_of_turn=True
            )

            # Wait for response
            async for response in session.receive():
                if response.data:
                    print(f"✅ Received audio response: {len(response.data)} bytes")
                    break

    except Exception as e:
        print(f"❌ Error: {str(e)}")

asyncio.run(test_live_api())
```

Run the test:

```bash
python test_live_api.py
```

Expected output:
```
✅ Successfully connected to Gemini Live API!
✅ Received audio response: XXXXX bytes
```

---

## Step 7: Run the Server

```bash
# Run Django development server with Daphne (for WebSocket support)
python manage.py runserver
```

Server will start at: `http://localhost:8000`

---

## Step 8: Test the API

### Using Postman

1. Import the Postman collection: `Audio_Chat_API.postman_collection.json`
2. Test endpoints:
   - Create Session: `POST /api/sessions/`
   - WebSocket: `ws://localhost:8000/ws/audio-chat/{session_id}/`

### Using curl

```bash
# Create a new chat session
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "level_description": "Test level with puzzles",
    "child_age": 7
  }'

# Response will include session_id
# Use it to connect via WebSocket
```

---

## Audio Format Requirements

### Input Audio (Client → Gemini)

```
Format: 16-bit PCM
Sample Rate: 16kHz
Channels: Mono (1 channel)
Encoding: Linear PCM
MIME Type: audio/pcm;rate=16000
```

### Output Audio (Gemini → Client)

```
Format: 16-bit PCM
Sample Rate: 24kHz
Channels: Mono (1 channel)
Encoding: Linear PCM
```

---

## Client-Side Implementation Example

### JavaScript WebSocket Client

```javascript
// Connect to WebSocket
const sessionId = 'your-session-id-here';
const ws = new WebSocket(`ws://localhost:8000/ws/audio-chat/${sessionId}/`);

ws.onopen = () => {
    console.log('Connected to audio chat');
};

ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // Binary audio data from Gemini (24kHz PCM)
        console.log('Received audio:', event.data);
        playAudio(event.data);
    } else {
        // Text data (JSON)
        const data = JSON.parse(event.data);
        console.log('Received:', data);
    }
};

// Send text message
function sendText(message) {
    ws.send(JSON.stringify({
        type: 'text',
        content: message
    }));
}

// Send audio data (16kHz PCM mono)
function sendAudio(audioBlob) {
    // Send as binary
    ws.send(audioBlob);
}
```

---

## Troubleshooting

### Error: "No module named 'google.genai'"

**Solution:** Install the NEW SDK:
```bash
pip install google-genai
```

### Error: "google-genai requires Python 3.9+"

**Solution:** Upgrade Python to 3.9 or higher (see Step 1)

### Error: "GEMINI_API_KEY is not configured"

**Solution:** Add your API key to `.env` file:
```env
GEMINI_API_KEY=your_api_key_here
```

### Error: "Connection refused" on WebSocket

**Solution:** Make sure the server is running with Daphne:
```bash
python manage.py runserver
```

### Error: "Live API connection failed"

**Possible causes:**
1. Invalid API key
2. API quota exceeded
3. Model not available in your region
4. Network connectivity issues

**Check:**
```bash
# Test API key
python test_live_api.py
```

---

## Project Structure

```
Drobe/
├── audio_chat/              # Main app
│   ├── models.py            # ChatSession, ChatMessage models
│   ├── views.py             # REST API endpoints
│   ├── consumers.py         # WebSocket consumer (NEW - uses Live API)
│   ├── serializers.py       # DRF serializers
│   ├── routing.py           # WebSocket routing
│   ├── services/
│   │   ├── __init__.py
│   │   └── gemini_live_service.py  # NEW google-genai SDK service
│   └── admin.py             # Admin panel configuration
├── Drobe/
│   ├── settings.py          # Django settings
│   ├── urls.py              # URL routing
│   ├── asgi.py              # ASGI configuration (WebSocket)
│   └── wsgi.py              # WSGI configuration
├── .env                     # Environment variables
├── manage.py                # Django management script
└── INSTALLATION.md          # This file
```

---

## Key Features Implemented

✅ **Gemini Live API Integration** - Uses NEW `google-genai` SDK
✅ **Native Audio Streaming** - Bidirectional real-time audio (no TTS/STT needed)
✅ **Conversation History** - Full context maintained across sessions
✅ **Multi-Modal Input** - Text, audio, and image support
✅ **Child-Friendly AI** - Age-appropriate responses (4-10 years)
✅ **WebSocket Support** - Real-time bidirectional communication
✅ **RESTful API** - Session management, history, screenshots
✅ **No Authentication** - Easy integration (except admin panel)

---

## Next Steps

1. Test the WebSocket connection
2. Implement client-side audio capture and playback
3. Test with real audio input/output
4. Deploy to production environment

---

## Resources

- [Gemini Live API Documentation](https://ai.google.dev/gemini-api/docs/live)
- [google-genai SDK GitHub](https://github.com/googleapis/python-genai)
- [Django Channels Documentation](https://channels.readthedocs.io/)
- [WebSocket API MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebSocket)

---

## Summary

**✅ Ready to Use:**
- Live API implementation complete
- Bidirectional audio streaming
- Full conversation history
- Child-friendly AI assistant
- WebSocket infrastructure

**⚠️ Requirements:**
- Python 3.9+ (CRITICAL)
- google-genai SDK
- Valid Gemini API key
- Client-side audio capture/playback

**🚀 Your implementation is production-ready once you upgrade to Python 3.9+!**

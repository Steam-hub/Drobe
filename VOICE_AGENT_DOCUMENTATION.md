# Voice Agent Application Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Key Features](#key-features)
4. [How It Works](#how-it-works)
5. [Setup & Installation](#setup--installation)
6. [Usage Guide](#usage-guide)
7. [Technical Details](#technical-details)
8. [API Reference](#api-reference)
9. [WebSocket Protocol](#websocket-protocol)
10. [Troubleshooting](#troubleshooting)

---

## Overview

The Voice Agent Application is a real-time, bidirectional audio streaming system that enables voice conversations between students and an AI assistant powered by Google's Gemini Live API. The application is designed for educational purposes, allowing children to interact naturally with an AI tutor using voice.

### Key Technologies
- **Backend**: Django 5.2.7 with Django Channels (WebSocket support)
- **AI Model**: Google Gemini 2.5 Flash Native Audio Preview
- **Frontend**: Vanilla JavaScript with Web Audio API
- **Audio Format**: PCM 16-bit, 16kHz (input) / 24kHz (output)
- **Protocol**: WebSocket for real-time bidirectional communication

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Browser)                        │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Microphone    │→ │ Audio        │→ │  WebSocket      │ │
│  │  Capture       │  │ Processing   │  │  Client         │ │
│  │  (Web Audio    │  │ (Resampling  │  │                 │ │
│  │   API)         │  │  to 16kHz)   │  │                 │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
│                                              ↕                │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Speaker       │← │ Audio        │← │  WebSocket      │ │
│  │  Playback      │  │ Queue        │  │  Messages       │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                Backend (Django + Channels)                   │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  WebSocket     │→ │ Audio Chat   │→ │  Gemini Live    │ │
│  │  Consumer      │  │ Consumer     │  │  Service        │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
│                                              ↕                │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  Database      │  │ Models       │  │  REST API       │ │
│  │  (SQLite)      │  │ (Sessions,   │  │  (DRF)          │ │
│  │                │  │  Messages)   │  │                 │ │
│  └────────────────┘  └──────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│              Google Gemini Live API (Cloud)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  • Native Audio Processing (16kHz PCM input)           │ │
│  │  • Built-in Voice Activity Detection (VAD)             │ │
│  │  • Natural Language Understanding                      │ │
│  │  • Text-to-Speech (Kore voice, 24kHz PCM output)      │ │
│  │  • Context Window Compression                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
Drobe/
├── audio_chat/                      # Main application
│   ├── consumers.py                 # WebSocket consumer for real-time audio
│   ├── models.py                    # Database models (ChatSession, ChatMessage)
│   ├── serializers.py               # REST API serializers
│   ├── views.py                     # REST API views + test page view
│   ├── urls.py                      # URL routing
│   ├── routing.py                   # WebSocket routing
│   └── services/
│       └── gemini_live_service.py   # Gemini Live API integration
├── templates/
│   └── voice_agent_test.html        # Frontend UI for testing
├── Drobe/
│   ├── settings.py                  # Django settings
│   ├── asgi.py                      # ASGI application for WebSockets
│   └── urls.py                      # Root URL configuration
└── db.sqlite3                       # SQLite database
```

---

## Key Features

### 1. Real-Time Bidirectional Audio Streaming
- **Continuous audio capture** from user's microphone
- **Automatic resampling** from browser's sample rate (typically 48kHz) to 16kHz for Gemini
- **Streaming response** from Gemini at 24kHz
- **Queue-based playback** to prevent overlapping audio

### 2. Voice Activity Detection (VAD)
- **Client-side VAD** for user interruption detection
- **Server-side VAD** (Gemini's built-in) for speech detection and turn management
- **Automatic turn completion** when user stops speaking

### 3. Initial Context Message
- **Pre-conversation setup** allows you to provide context to the AI before the student speaks
- **Customizable greeting** and behavior instructions
- **Audio response** from AI immediately upon connection

### 4. Session Management
- **Persistent chat sessions** stored in database
- **Chat history** loaded automatically when reconnecting
- **Session metadata**: level description, child age, timestamps

### 5. Child-Friendly AI Configuration
- **Age-appropriate language** (configured for ages 4-10)
- **Supportive tone** with positive reinforcement
- **Educational focus** with gentle guidance
- **Kore voice** for natural, friendly interaction

---

## How It Works

### Connection Flow

```
1. User opens test page → /audio-chat/test/
2. User enters initial message (optional)
3. User clicks "Connect & Start"
4. Frontend:
   - Creates new session via POST /api/sessions/
   - Requests microphone access
   - Establishes WebSocket connection to /ws/audio-chat/{session_id}/
5. Backend (Consumer):
   - Validates session
   - Loads chat history from database
   - Initializes GeminiLiveService with initial_message
   - Connects to Gemini Live API
   - Sends initial_message to Gemini (if provided)
6. Gemini:
   - Receives initial context
   - Generates audio greeting
   - Streams audio response back
7. Backend:
   - Receives audio chunks from Gemini
   - Forwards to WebSocket client
8. Frontend:
   - Queues audio chunks
   - Plays sequentially through speakers
9. User speaks → Audio capture begins
```

### Audio Streaming Flow (User → AI)

```
1. Browser captures audio via Web Audio API (ScriptProcessor)
   - Sample Rate: 48kHz (browser default)
   - Format: Float32Array

2. Frontend resampling
   - Downsample from 48kHz → 16kHz using linear interpolation
   - Convert Float32 → Int16 PCM
   - Chunk size: 1024 samples

3. WebSocket transmission
   - Send as binary ArrayBuffer
   - Continuous stream (including silence)

4. Backend (Consumer)
   - Receive binary audio data
   - Forward to GeminiLiveService.send_audio()

5. Gemini Live API
   - Built-in VAD detects speech
   - Processes audio with NLU
   - Determines when user stops speaking (automatic turn detection)
   - Generates response

6. Response flows back (see next section)
```

### Audio Streaming Flow (AI → User)

```
1. Gemini generates audio response
   - Format: PCM 16-bit, 24kHz
   - Streamed in chunks

2. Backend (GeminiLiveService)
   - Receives via async iterator (receive_responses)
   - Yields audio chunks as they arrive
   - Detects turn_complete signal

3. Backend (Consumer)
   - Forwards audio chunks to WebSocket as binary
   - Sends turn_complete as JSON

4. Frontend
   - Receives binary audio → adds to queue
   - Queue-based playback:
     - Convert Int16 PCM → Float32
     - Create AudioBuffer at 24kHz
     - Play via Web Audio API
   - Sequential playback prevents overlap

5. User hears response through speakers
```

### Turn Management

**Google's Pattern** (what we use):
- Send **continuous audio stream** (including silence) to Gemini
- **Gemini's built-in VAD** automatically detects:
  - When user starts speaking
  - When user stops speaking (pause/silence)
- **No manual end-of-turn signaling needed** for audio
- Gemini automatically generates response after detecting silence

**Turn Complete Signal**:
- After each AI response, Gemini sends `turn_complete`
- Frontend uses this to:
  - Log turn completion
  - Maintain conversation flow
  - Clear audio queue ONLY on user interruption

---

## Setup & Installation

### Prerequisites
- Python 3.9+
- Google Gemini API Key
- Modern web browser with microphone access

### Installation Steps

1. **Clone the repository**
```bash
cd C:\Users\OSAMA\SteamHubGame\Drobe
```

2. **Create virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install django==5.2.7
pip install channels
pip install daphne
pip install djangorestframework
pip install django-cors-headers
pip install google-genai
pip install python-dotenv
```

4. **Configure environment variables**

Create `.env` file in project root:
```env
GEMINI_API_KEY=your_api_key_here
```

5. **Run migrations**
```bash
python manage.py makemigrations
python manage.py migrate
```

6. **Start the server**
```bash
python manage.py runserver
```

7. **Access the test interface**
```
http://127.0.0.1:8000/audio-chat/test/
```

---

## Usage Guide

### Testing the Voice Agent

1. **Open the test page**
   - Navigate to `http://127.0.0.1:8000/audio-chat/test/`

2. **Leave Session ID empty** (to create new session)

3. **Enter Initial Message** (optional)
   - Example: "You are helping a 10-year-old with math. Greet them warmly and ask what they'd like to learn."

4. **Click "Connect & Start"**
   - Browser will request microphone permission
   - Session will be created automatically
   - WebSocket connection established
   - AI will greet you (if initial message provided)

5. **Speak naturally**
   - Audio is captured continuously
   - Gemini detects when you start/stop speaking
   - AI responds automatically after you pause

6. **Monitor logs**
   - Connection status
   - Audio chunks sent/received
   - Turn completion signals
   - Errors (if any)

7. **Disconnect**
   - Click "Disconnect" button
   - Or close the browser tab

### Creating Sessions via API

**Endpoint**: `POST /api/sessions/`

**Request Body**:
```json
{
  "level_description": "Learning fractions",
  "child_age": 8,
  "initial_message": "Greet the student and ask what they know about fractions."
}
```

**Response**:
```json
{
  "id": "3c17ed5a-aa78-4b4d-8ccc-6f552203a1bd",
  "level_description": "Learning fractions",
  "child_age": 8,
  "initial_message": "Greet the student and ask what they know about fractions.",
  "created_at": "2025-10-12T22:00:00Z",
  "updated_at": "2025-10-12T22:00:00Z",
  "is_active": true
}
```

---

## Technical Details

### Audio Specifications

| Parameter | Value | Description |
|-----------|-------|-------------|
| **Input Format** | PCM 16-bit mono | Raw audio format sent to Gemini |
| **Input Sample Rate** | 16kHz | Required by Gemini Live API |
| **Output Format** | PCM 16-bit mono | Raw audio format from Gemini |
| **Output Sample Rate** | 24kHz | Gemini's response audio rate |
| **Browser Capture Rate** | 48kHz (typical) | Web Audio API default |
| **Chunk Size** | 1024 samples | Per audio processing cycle |
| **VAD Threshold** | 0.02 | Audio energy threshold for interruption detection |

### Gemini Live API Configuration

```python
CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],           # Audio-only responses
    media_resolution="MEDIA_RESOLUTION_MEDIUM",  # Balanced quality
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Kore"            # Child-friendly voice
            )
        )
    ),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=25600,                # Start compression at 25.6k tokens
        sliding_window=types.SlidingWindow(
            target_tokens=12800              # Compress to 12.8k tokens
        ),
    ),
)
```

### Audio Resampling Algorithm

The application uses **linear interpolation** for resampling:

```javascript
function downsampleTo16kHz(audioData, sourceSampleRate) {
    const targetSampleRate = 16000;
    const sampleRateRatio = sourceSampleRate / targetSampleRate;
    const newLength = Math.round(audioData.length / sampleRateRatio);
    const result = new Float32Array(newLength);

    for (let i = 0; i < newLength; i++) {
        const srcIndex = i * sampleRateRatio;
        const srcIndexFloor = Math.floor(srcIndex);
        const srcIndexCeil = Math.min(srcIndexFloor + 1, audioData.length - 1);
        const t = srcIndex - srcIndexFloor;

        // Linear interpolation
        result[i] = audioData[srcIndexFloor] * (1 - t) + audioData[srcIndexCeil] * t;
    }

    return result;
}
```

### PCM Conversion

**Float32 → Int16 PCM** (for sending to Gemini):
```javascript
const pcmData = new Int16Array(audioData.length);
for (let i = 0; i < audioData.length; i++) {
    const s = Math.max(-1, Math.min(1, audioData[i]));
    pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
}
```

**Int16 PCM → Float32** (for playback):
```javascript
for (let i = 0; i < int16Array.length; i++) {
    const sample = int16Array[i];
    float32Array[i] = sample < 0 ? sample / 32768.0 : sample / 32767.0;
}
```

---

## API Reference

### REST API Endpoints

#### 1. Create Session
**POST** `/api/sessions/`

**Request**:
```json
{
  "level_description": "string",
  "child_age": 7,
  "initial_message": "string (optional)"
}
```

**Response**: 201 Created
```json
{
  "id": "uuid",
  "level_description": "string",
  "child_age": 7,
  "initial_message": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "is_active": true
}
```

#### 2. Get Session
**GET** `/api/sessions/{session_id}/`

**Response**: 200 OK
```json
{
  "id": "uuid",
  "level_description": "string",
  "child_age": 7,
  "initial_message": "string",
  "created_at": "datetime",
  "updated_at": "datetime",
  "is_active": true
}
```

#### 3. List Sessions
**GET** `/api/sessions/`

**Response**: 200 OK
```json
[
  {
    "id": "uuid",
    "level_description": "string",
    "child_age": 7,
    "created_at": "datetime",
    "is_active": true
  }
]
```

#### 4. Get Chat History
**GET** `/api/sessions/{session_id}/history/`

**Response**: 200 OK
```json
{
  "session_id": "uuid",
  "messages": [
    {
      "id": "uuid",
      "sender": "child|assistant",
      "message_type": "text|audio",
      "text_content": "string",
      "created_at": "datetime"
    }
  ]
}
```

---

## WebSocket Protocol

### Connection URL
```
ws://127.0.0.1:8000/ws/audio-chat/{session_id}/
```

### Message Types

#### 1. Connection Confirmation (Server → Client)
**Type**: JSON
```json
{
  "type": "connection",
  "message": "Connected to Gemini Live API with native audio streaming",
  "session_id": "uuid",
  "history_message_count": 5,
  "model": "gemini-2.5-flash-native-audio-preview-09-2025",
  "audio_format": "PCM 16kHz 16-bit mono (input), 24kHz mono (output)"
}
```

#### 2. Audio Data (Client → Server)
**Type**: Binary (ArrayBuffer)
- Format: Int16 PCM, 16kHz, mono
- Sent continuously (including silence)

#### 3. Audio Data (Server → Client)
**Type**: Binary (ArrayBuffer)
- Format: Int16 PCM, 24kHz, mono
- Streamed in chunks as generated by Gemini

#### 4. Text Response (Server → Client)
**Type**: JSON
```json
{
  "type": "response",
  "content": "string",
  "session_id": "uuid"
}
```

#### 5. Turn Complete (Server → Client)
**Type**: JSON
```json
{
  "type": "turn_complete",
  "session_id": "uuid"
}
```

#### 6. Error (Server → Client)
**Type**: JSON
```json
{
  "type": "error",
  "message": "Error description",
  "error": "Detailed error message"
}
```

#### 7. Ping/Pong (Keepalive)
**Client → Server**:
```json
{
  "type": "ping"
}
```

**Server → Client**:
```json
{
  "type": "pong"
}
```

---

## Troubleshooting

### Common Issues

#### 1. No Response from AI

**Symptoms**: Audio is sent but no response received

**Possible Causes**:
- Invalid API key
- Gemini API quota exceeded
- Incorrect audio format
- Network issues

**Solutions**:
- Check `GEMINI_API_KEY` in `.env`
- Verify API quota at Google AI Studio
- Check browser console for errors
- Monitor Django server logs

**Logs to Check**:
```
DEBUG Sent audio chunk: 682 bytes (format: 16kHz PCM)
INFO 🛑 Signaled end of turn to Gemini
ERROR ❌ Error receiving responses: [error details]
```

#### 2. WebSocket Connection Failed

**Symptoms**: "No route found for path" or "WebSocket disconnected"

**Possible Causes**:
- Invalid session ID
- Session doesn't exist
- Server not running

**Solutions**:
- Leave Session ID field empty to create new session
- Verify session exists: `GET /api/sessions/{id}/`
- Ensure server is running with Daphne (not runserver without channels)

#### 3. Microphone Access Denied

**Symptoms**: "Error: Permission denied"

**Solutions**:
- Click "Allow" when browser prompts for microphone
- Check browser settings → Privacy → Microphone
- Try HTTPS instead of HTTP (required by some browsers)

#### 4. Audio Quality Issues / Noise

**Symptoms**: Noisy, distorted, or robotic audio

**Possible Causes**:
- Incorrect sample rate conversion
- PCM conversion errors
- Audio buffer issues

**Solutions**:
- Verify resampling is working: Check log for "Audio capture sample rate: 48000 Hz"
- Check audio energy threshold (should be > 0.02 when speaking)
- Clear browser cache and reload

#### 5. Error 1007: Invalid Frame Payload

**Symptoms**: WebSocket closes with error 1007

**Possible Causes**:
- Wrong audio format sent to Gemini
- Incorrect mime_type
- Manual end_of_turn signaling (not needed for audio)

**Solutions**:
- Ensure audio is 16kHz PCM before sending
- Verify `mime_type: "audio/pcm"` in data
- Don't send manual end_of_turn for audio streams

### Debug Mode

Enable detailed logging in `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'audio_chat': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Change to DEBUG for detailed logs
        },
    },
}
```

### Useful Log Messages

| Log Message | Meaning |
|-------------|---------|
| ✅ Live session started | Gemini connection successful |
| 📤 Sending initial context message | Initial message being sent |
| 📥 Received audio from client: X bytes | Audio received from browser |
| Sent audio chunk: X bytes (format: 16kHz PCM) | Audio sent to Gemini |
| 🎧 Starting to listen for responses | Listening for Gemini's response |
| Received audio chunk: X bytes | Audio received from Gemini |
| ✅ Turn complete | AI finished speaking |
| ❌ Error receiving responses | Connection or API error |

---

## Best Practices

### For Developers

1. **Always use continuous audio streaming** - Don't filter silence on client-side
2. **Let Gemini handle VAD** - Its built-in VAD is optimized for speech detection
3. **Queue audio playback** - Prevents overlapping responses
4. **Handle interruptions gracefully** - Clear queue when user speaks during AI response
5. **Use proper audio formats** - 16kHz PCM input, 24kHz PCM output
6. **Store chat history** - Enables context persistence across sessions

### For Initial Messages

Good examples:
- "You are a friendly math tutor. Greet the student and ask what they're learning."
- "The student needs help with reading. Start with an encouraging introduction."
- "Introduce yourself as their science helper and ask about their favorite topic."

Avoid:
- Very long messages (keep under 200 words)
- Technical jargon in student-facing messages
- Conflicting instructions with system prompt

### Security Considerations

1. **API Key Protection**:
   - Store in `.env` file (not in code)
   - Never commit `.env` to version control
   - Add `.env` to `.gitignore`

2. **Session Validation**:
   - Always validate session exists before connecting
   - Check `is_active` status
   - Implement rate limiting for session creation

3. **Audio Data**:
   - Validate audio chunk sizes
   - Implement maximum session duration
   - Clean up old audio files periodically

---

## Future Enhancements

Potential improvements:
- [ ] Add text chat alongside voice
- [ ] Support for screenshots/images during conversation
- [ ] Session recording and playback
- [ ] Multi-language support
- [ ] Parent/teacher dashboard
- [ ] Analytics and learning insights
- [ ] Mobile app support
- [ ] Group sessions (multiple students)

---

## Support & Resources

- **Google Gemini Live API Docs**: https://ai.google.dev/gemini-api/docs
- **Django Channels Docs**: https://channels.readthedocs.io/
- **Web Audio API**: https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API
- **Project Repository**: [Your repository URL]

---

## License

[Your license information]

---

**Last Updated**: October 12, 2025
**Version**: 1.0.0

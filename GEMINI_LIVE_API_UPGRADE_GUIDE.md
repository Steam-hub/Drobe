# Gemini Live API - Native Audio Implementation Guide

## Current Status

### ✅ What's Implemented
- Model name updated to: `gemini-2.5-flash-native-audio-preview-09-2025`
- Chat session with full conversation history
- WebSocket infrastructure for real-time communication
- Text-based chat fully functional
- Automatic fallback to `gemini-2.0-flash` if native audio unavailable

### ❌ What's Missing (Python 3.8 Limitation)
- **Gemini Live API** requires **Python 3.9+**
- Cannot use `google-genai` SDK (only available for Python 3.9+)
- Real-time bidirectional audio streaming not available
- Native audio input/output requires Live API

## The Problem

The native audio model `gemini-2.5-flash-native-audio-preview-09-2025` requires the **Gemini Live API**, which is only available through the new `google-genai` SDK.

**Requirement:**
```bash
# Required for Live API
pip install google-genai  # Requires Python 3.9+

# Current environment
Python 3.8.10  # ❌ Not compatible
```

## Solution: Upgrade to Python 3.9+

### Step 1: Upgrade Python

```bash
# Windows
# Download Python 3.11+ from python.org
# Install and verify
python --version  # Should show 3.9+ or higher

# Linux/Mac
sudo apt update
sudo apt install python3.11
```

### Step 2: Install New SDK

```bash
# Uninstall old SDK
pip uninstall google-generativeai

# Install new SDK
pip install google-genai

# Install additional requirements
pip install websockets asyncio
```

### Step 3: Update Code for Live API

Replace `audio_chat/services/gemini_live_service.py` with the following implementation:

```python
"""
Gemini Live API Service with Native Audio Streaming
Requires: google-genai (Python 3.9+)
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiLiveAudioService:
    """
    Service for Gemini Live API with native audio streaming
    """

    def __init__(self, session_id: str, level_description: str, child_age: int = 7, history: Optional[List] = None):
        self.session_id = session_id
        self.level_description = level_description
        self.child_age = child_age
        self.api_key = settings.GEMINI_API_KEY

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured")

        # Create client
        self.client = genai.Client(api_key=self.api_key)

        # Model configuration
        self.model = 'gemini-2.5-flash-native-audio-preview-09-2025'

        # System instruction
        self.system_instruction = self._build_system_instruction()

        # Chat history
        self.history = history or []

        # Live session (will be created when needed)
        self.live_session = None

    def _build_system_instruction(self) -> str:
        return f"""You are a friendly, helpful AI assistant for children aged {self.child_age}.

Current Game Level: {self.level_description}

Guidelines:
- Use simple, age-appropriate language
- Be patient, positive, and encouraging
- Give hints, not direct answers
- Celebrate their efforts
- Keep responses short and clear"""

    async def start_live_session(self):
        """
        Start a Live API session for real-time audio streaming
        """
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],  # or ["AUDIO", "TEXT"]
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Charon"  # Child-friendly voice
                    )
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part(text=self.system_instruction)]
            )
        )

        # Connect to Live API
        self.live_session = await self.client.aio.live.connect(
            model=self.model,
            config=config
        )

        logger.info(f"Live session started for {self.session_id}")
        return self.live_session

    async def send_audio(self, audio_bytes: bytes):
        """
        Send audio data to Gemini Live API

        Args:
            audio_bytes: PCM audio data (16-bit, 16kHz, mono)
        """
        if not self.live_session:
            await self.start_live_session()

        await self.live_session.send_realtime_input(
            audio=types.Blob(
                data=audio_bytes,
                mime_type="audio/pcm;rate=16000"
            )
        )

    async def receive_audio_stream(self):
        """
        Receive audio responses from Gemini Live API

        Yields:
            Audio chunks and metadata
        """
        if not self.live_session:
            await self.start_live_session()

        async for response in self.live_session.receive():
            if response.data:
                yield {
                    'type': 'audio',
                    'data': response.data,  # Audio bytes
                    'session_id': self.session_id
                }
            if response.text:
                yield {
                    'type': 'text',
                    'content': response.text,
                    'session_id': self.session_id
                }

    async def send_text(self, text: str) -> Dict[str, Any]:
        """
        Send text message via Live API
        """
        if not self.live_session:
            await self.start_live_session()

        await self.live_session.send(
            types.LiveClientContent(
                turns=[
                    types.LiveClientTurn(
                        role="user",
                        parts=[types.Part(text=text)]
                    )
                ],
                turn_complete=True
            )
        )

        return {"success": True, "session_id": self.session_id}

    async def close_session(self):
        """
        Close the Live API session
        """
        if self.live_session:
            await self.live_session.close()
            logger.info(f"Live session closed for {self.session_id}")
```

### Step 4: Update WebSocket Consumer

Update `audio_chat/consumers.py` to use the Live API:

```python
class AudioChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.session = await self.get_session(self.session_id)

        if not self.session:
            await self.close(code=4004)
            return

        # Load history
        chat_history = await self.load_chat_history()

        # Initialize Live API service
        self.gemini_live_service = GeminiLiveAudioService(
            session_id=str(self.session.id),
            level_description=self.session.level_description,
            child_age=self.session.child_age,
            history=chat_history
        )

        # Start Live session
        await self.gemini_live_service.start_live_session()

        # Start listening for responses
        asyncio.create_task(self.listen_for_responses())

        await self.accept()
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to Live API with native audio',
            'session_id': str(self.session.id)
        }))

    async def listen_for_responses(self):
        """
        Listen for responses from Gemini Live API
        """
        async for response in self.gemini_live_service.receive_audio_stream():
            if response['type'] == 'audio':
                # Send audio back to client
                await self.send(bytes_data=response['data'])
            elif response['type'] == 'text':
                # Send text response
                await self.send(text_data=json.dumps({
                    'type': 'response',
                    'content': response['content']
                }))

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data:
            # Send audio to Gemini
            await self.gemini_live_service.send_audio(bytes_data)
        elif text_data:
            data = json.loads(text_data)
            if data.get('type') == 'text':
                await self.gemini_live_service.send_text(data['content'])

    async def disconnect(self, close_code):
        await self.gemini_live_service.close_session()
```

## Audio Format Requirements

### Input Audio (Client → Gemini)
```
Format: 16-bit PCM
Sample Rate: 16kHz
Channels: Mono (1 channel)
MIME Type: audio/pcm;rate=16000
```

### Output Audio (Gemini → Client)
```
Format: Opus or PCM
Sample Rate: 24kHz
Channels: Mono (1 channel)
```

## Client-Side JavaScript Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/audio-chat/{sessionId}/');

// Get microphone access
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const mediaRecorder = new MediaRecorder(stream);

// Send audio chunks
mediaRecorder.ondataavailable = async (event) => {
    if (event.data.size > 0) {
        // Convert to PCM 16kHz mono
        const audioBuffer = await event.data.arrayBuffer();
        const pcmData = convertToPCM(audioBuffer);  // Your conversion function

        // Send to WebSocket
        ws.send(pcmData);
    }
};

// Receive audio responses
ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // Audio response - play it
        playAudio(event.data);
    } else {
        // Text response
        const data = JSON.parse(event.data);
        console.log(data.content);
    }
};

// Start recording
mediaRecorder.start(100);  // Send chunks every 100ms
```

## Testing Live API

### Test 1: Verify Python Version

```bash
python --version  # Must be 3.9+
```

### Test 2: Verify SDK Installation

```bash
python -c "from google import genai; print('SDK OK')"
```

### Test 3: Test Live Connection

```python
import asyncio
from google import genai
from google.genai import types

async def test_live_api():
    client = genai.Client(api_key="YOUR_API_KEY")

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"]
    )

    async with client.aio.live.connect(
        model="gemini-2.5-flash-native-audio-preview-09-2025",
        config=config
    ) as session:
        print("✅ Live API connection successful!")

        # Send test audio
        await session.send_realtime_input(
            audio=types.Blob(
                data=b"test_audio_data",
                mime_type="audio/pcm;rate=16000"
            )
        )

        # Receive response
        async for response in session.receive():
            print(f"✅ Received: {response}")
            break

asyncio.run(test_live_api())
```

## Migration Checklist

- [ ] Upgrade Python to 3.9+
- [ ] Install `google-genai` SDK
- [ ] Update `gemini_live_service.py` with Live API code
- [ ] Update `consumers.py` for bidirectional streaming
- [ ] Test audio input/output formats
- [ ] Update client-side JavaScript for audio capture
- [ ] Test full audio conversation flow
- [ ] Update Postman collection with audio examples
- [ ] Deploy with updated dependencies

## Benefits of Live API

✅ **Real-time bidirectional audio** - True voice conversation
✅ **Native audio processing** - No STT/TTS needed
✅ **Lower latency** - Optimized for real-time
✅ **Better voice quality** - 24kHz output
✅ **Emotion detection** - Affective dialogue support
✅ **Interruption handling** - Natural conversation flow

## Resources

- [Gemini Live API Documentation](https://ai.google.dev/gemini-api/docs/live)
- [google-genai SDK Documentation](https://github.com/googleapis/python-genai)
- [Live API Demo](https://aistudio.google.com/live)
- [WebSocket Examples](https://github.com/google-gemini/cookbook/tree/main/quickstarts/websockets)

## Summary

**Current Implementation:**
- ✅ Uses `gemini-2.5-flash-native-audio-preview-09-2025` model name
- ✅ Falls back to `gemini-2.0-flash` on Python 3.8
- ✅ Chat history fully functional
- ✅ WebSocket infrastructure ready

**To Enable Native Audio:**
1. Upgrade to Python 3.9+
2. Install `google-genai` SDK
3. Replace service code with Live API implementation
4. Update consumer for bidirectional audio streaming
5. Test with real audio input/output

The codebase is **ready for upgrade** - just need Python 3.9+! 🚀

# Testing Guide - Audio Chat API

Complete guide for testing all API endpoints and WebSocket functionality.

---

## Prerequisites

Before testing, make sure:

- [ ] Server is running: `python manage.py runserver`
- [ ] Python 3.9+ installed
- [ ] google-genai SDK installed
- [ ] GEMINI_API_KEY configured in `.env`
- [ ] You have a session_id (create one first)

---

## Part 1: REST API Testing

### Method A: Using curl (Command Line)

#### 1. Health Check

```bash
curl http://localhost:8000/api/health/
```

**Expected Response:**
```json
{
    "status": "ok",
    "message": "Audio Chat API is running"
}
```

---

#### 2. Create Chat Session

```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d "{
    \"level_description\": \"Level 3: Collect 5 stars by jumping over obstacles\",
    \"child_age\": 7
  }"
```

**Expected Response:**
```json
{
    "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "level_description": "Level 3: Collect 5 stars by jumping over obstacles",
    "child_age": 7,
    "created_at": "2025-01-15T10:30:00.123456Z",
    "is_active": true
}
```

**⚠️ SAVE THE `id` - YOU'LL NEED IT FOR ALL OTHER TESTS!**

---

#### 3. List All Active Sessions

```bash
curl http://localhost:8000/api/sessions/
```

**Expected Response:**
```json
[
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "level_description": "Level 3: Collect 5 stars...",
        "child_age": 7,
        "created_at": "2025-01-15T10:30:00.123456Z",
        "is_active": true
    }
]
```

---

#### 4. Get Session Details

```bash
# Replace SESSION_ID with actual ID from step 2
curl http://localhost:8000/api/sessions/SESSION_ID/
```

**Expected Response:**
```json
{
    "id": "SESSION_ID",
    "level_description": "Level 3: Collect 5 stars...",
    "child_age": 7,
    "created_at": "2025-01-15T10:30:00.123456Z",
    "is_active": true
}
```

---

#### 5. Upload Screenshot

```bash
# Replace SESSION_ID with actual ID
curl -X POST http://localhost:8000/api/screenshot/ \
  -F "session_id=SESSION_ID" \
  -F "image=@test_screenshot.png" \
  -F "question=What should I do here?"
```

**Expected Response:**
```json
{
    "success": true,
    "message": "Screenshot analyzed successfully",
    "ai_response": "I can see you're at the jumping puzzle. Try jumping over the blue platform first...",
    "session_id": "SESSION_ID"
}
```

---

#### 6. Get Chat History

```bash
# Replace SESSION_ID with actual ID
curl "http://localhost:8000/api/history/?session_id=SESSION_ID&limit=50"
```

**Expected Response:**
```json
{
    "success": true,
    "session_id": "SESSION_ID",
    "message_count": 2,
    "messages": [
        {
            "id": 1,
            "sender": "child",
            "message_type": "text",
            "text_content": "I need help",
            "created_at": "2025-01-15T10:31:00Z"
        },
        {
            "id": 2,
            "sender": "assistant",
            "message_type": "text",
            "text_content": "Of course! What do you need help with?",
            "created_at": "2025-01-15T10:31:01Z"
        }
    ]
}
```

---

#### 7. End Session

```bash
# Replace SESSION_ID with actual ID
curl -X POST http://localhost:8000/api/sessions/SESSION_ID/end_session/
```

**Expected Response:**
```json
{
    "message": "Session ended successfully",
    "session_id": "SESSION_ID"
}
```

---

### Method B: Using Postman

1. **Import Collection:**
   - Open Postman
   - Click "Import"
   - Select `Audio_Chat_API.postman_collection.json`

2. **Set Base URL:**
   - Already configured: `http://localhost:8000`

3. **Run Tests:**
   - Start with "Health Check"
   - Then "Create Chat Session" (saves session_id automatically)
   - Test other endpoints using saved session_id

---

## Part 2: WebSocket Testing

### Method A: Using Browser Console

#### Step 1: Open Browser Console

1. Open Chrome/Firefox/Edge
2. Press F12 to open Developer Tools
3. Go to "Console" tab

#### Step 2: Create WebSocket Connection

```javascript
// Replace SESSION_ID with your actual session ID
const sessionId = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890';
const ws = new WebSocket(`ws://localhost:8000/ws/audio-chat/${sessionId}/`);

ws.onopen = () => {
    console.log('✅ Connected to Live API!');
};

ws.onmessage = (event) => {
    if (event.data instanceof Blob) {
        // Binary audio response
        console.log('🎵 Received audio:', event.data.size, 'bytes');
        // In real app, you would play this audio
    } else {
        // Text response
        const data = JSON.parse(event.data);
        console.log('📩 Received:', data);
    }
};

ws.onerror = (error) => {
    console.error('❌ WebSocket error:', error);
};

ws.onclose = (event) => {
    console.log('🔌 WebSocket closed:', event.code, event.reason);
};
```

**Expected Console Output:**
```
✅ Connected to Live API!
📩 Received: {
    type: "connection",
    message: "Connected to Gemini Live API with native audio streaming",
    session_id: "...",
    history_message_count: 0,
    model: "gemini-2.5-flash-native-audio-preview-09-2025",
    audio_format: "PCM 16kHz 16-bit mono (input), 24kHz mono (output)"
}
```

---

#### Step 3: Send Text Message

```javascript
// Send a text message
ws.send(JSON.stringify({
    type: 'text',
    content: 'Hello! Can you help me with this level?'
}));
```

**Expected Response:**
```javascript
📩 Received: {
    type: "response",
    content: "Hi there! I'd be happy to help you! What's challenging you in this level?",
    session_id: "..."
}
```

---

#### Step 4: Test Ping/Pong

```javascript
// Test keepalive
ws.send(JSON.stringify({
    type: 'ping'
}));

// Expected response:
// 📩 Received: { type: "pong" }
```

---

### Method B: Using Python Script

Create a file `test_websocket.py`:

```python
import asyncio
import websockets
import json

async def test_websocket():
    # Replace with your session ID
    session_id = 'a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    uri = f'ws://localhost:8000/ws/audio-chat/{session_id}/'

    async with websockets.connect(uri) as websocket:
        print('✅ Connected to WebSocket')

        # Wait for connection message
        response = await websocket.recv()
        print('📩 Connection message:', response)

        # Send text message
        message = {
            'type': 'text',
            'content': 'Hello! I need help with the puzzle.'
        }
        await websocket.send(json.dumps(message))
        print('📤 Sent:', message)

        # Wait for response
        response = await websocket.recv()
        print('📩 Received:', response)

# Run test
asyncio.run(test_websocket())
```

Run it:
```bash
pip install websockets
python test_websocket.py
```

**Expected Output:**
```
✅ Connected to WebSocket
📩 Connection message: {"type":"connection","message":"Connected to Gemini Live API..."}
📤 Sent: {'type': 'text', 'content': 'Hello! I need help with the puzzle.'}
📩 Received: {"type":"response","content":"Hi there! I'd love to help..."}
```

---

### Method C: Using WebSocket Client Tool

#### Option 1: Simple WebSocket Client (Browser Extension)

1. Install "Simple WebSocket Client" extension (Chrome/Firefox)
2. Open the extension
3. Enter URL: `ws://localhost:8000/ws/audio-chat/SESSION_ID/`
4. Click "Connect"
5. Send messages in JSON format

#### Option 2: websocat (Command Line)

```bash
# Install websocat
# Windows: Download from https://github.com/vi/websocat/releases
# Linux: sudo apt install websocat
# Mac: brew install websocat

# Connect
websocat ws://localhost:8000/ws/audio-chat/SESSION_ID/

# Type messages:
{"type": "text", "content": "Hello!"}
```

---

## Part 3: Audio Streaming Testing

### Test Audio Input (Advanced)

**Note:** This requires proper audio capture implementation on the client side.

```javascript
// Get microphone access
navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        const audioContext = new AudioContext({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(stream);

        // You need to implement:
        // 1. Convert to 16-bit PCM
        // 2. Downsample to 16kHz
        // 3. Convert to mono
        // 4. Send to WebSocket

        // For now, just log:
        console.log('✅ Microphone access granted');
        console.log('Sample rate:', audioContext.sampleRate);
    })
    .catch(error => {
        console.error('❌ Microphone access denied:', error);
    });
```

**Audio Format Requirements:**
- Format: 16-bit Linear PCM
- Sample Rate: 16kHz
- Channels: Mono (1 channel)
- Send as: Binary WebSocket message

---

## Part 4: Integration Testing

### Complete Test Flow

```javascript
// Step 1: Create session via REST API
fetch('http://localhost:8000/api/sessions/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        level_description: 'Test level',
        child_age: 7
    })
})
.then(res => res.json())
.then(session => {
    console.log('✅ Session created:', session.id);

    // Step 2: Connect WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/audio-chat/${session.id}/`);

    ws.onopen = () => {
        console.log('✅ WebSocket connected');

        // Step 3: Send message
        ws.send(JSON.stringify({
            type: 'text',
            content: 'Test message'
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('✅ Received response:', data);

        // Step 4: Get history
        fetch(`http://localhost:8000/api/history/?session_id=${session.id}`)
            .then(res => res.json())
            .then(history => {
                console.log('✅ Chat history:', history);

                // Step 5: End session
                ws.close();

                return fetch(`http://localhost:8000/api/sessions/${session.id}/end_session/`, {
                    method: 'POST'
                });
            })
            .then(() => {
                console.log('✅ Test flow complete!');
            });
    };
});
```

---

## Part 5: Error Testing

### Test Invalid Session

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/audio-chat/invalid-id/');

ws.onclose = (event) => {
    console.log('Expected error - Invalid session:', event.code);
    // Expected: code 4004
};
```

### Test Without API Key

1. Temporarily remove `GEMINI_API_KEY` from `.env`
2. Restart server
3. Try connecting to WebSocket

**Expected Error:**
```json
{
    "type": "error",
    "message": "GEMINI_API_KEY is not configured in settings"
}
```

### Test Python Version Issue

If you're on Python 3.8:

**Expected Error:**
```json
{
    "type": "error",
    "message": "Failed to connect to Gemini Live API",
    "error": "...",
    "note": "Live API requires Python 3.9+ and google-genai package"
}
```

---

## Part 6: Performance Testing

### Test Response Time

```javascript
const startTime = Date.now();

ws.send(JSON.stringify({
    type: 'text',
    content: 'Quick test'
}));

ws.onmessage = (event) => {
    const endTime = Date.now();
    const responseTime = endTime - startTime;
    console.log(`⏱️ Response time: ${responseTime}ms`);
};
```

### Test Multiple Messages

```javascript
for (let i = 0; i < 5; i++) {
    ws.send(JSON.stringify({
        type: 'text',
        content: `Message ${i + 1}`
    }));
}
```

---

## Part 7: Troubleshooting Tests

### Check Server Logs

While testing, watch the server console for logs:

```
INFO: WebSocket connected for session abc123 with 0 historical messages
INFO: ✅ Live session started for abc123
INFO: Sent text response to client
```

### Check Django Admin

1. Go to http://localhost:8000/admin/
2. Navigate to "Chat messages"
3. Verify messages are being saved

### Test Database

```bash
python manage.py shell
```

```python
from audio_chat.models import ChatSession, ChatMessage

# Get all sessions
sessions = ChatSession.objects.all()
print(f"Total sessions: {sessions.count()}")

# Get messages for a session
session = ChatSession.objects.first()
messages = ChatMessage.objects.filter(session=session)
print(f"Messages: {messages.count()}")

for msg in messages:
    print(f"{msg.sender}: {msg.text_content}")
```

---

## Testing Checklist

Use this checklist to verify everything works:

### REST API
- [ ] Health check returns OK
- [ ] Can create chat session
- [ ] Can list sessions
- [ ] Can get session details
- [ ] Can upload screenshot
- [ ] Can retrieve chat history
- [ ] Can end session

### WebSocket
- [ ] Can connect to WebSocket
- [ ] Receives connection message with Live API info
- [ ] Can send text message
- [ ] Receives text response
- [ ] Ping/pong works
- [ ] Connection closes cleanly

### Live API
- [ ] Connection message shows Live API model
- [ ] Audio format information present
- [ ] History count correct

### Database
- [ ] Sessions saved to database
- [ ] Messages saved to database
- [ ] History persists across connections

### Admin Panel
- [ ] Can login to admin
- [ ] Can view sessions
- [ ] Can view messages
- [ ] Can manage data

---

## Common Test Failures

### ❌ "Connection refused"

**Cause:** Server not running

**Fix:**
```bash
python manage.py runserver
```

---

### ❌ "No module named 'google.genai'"

**Cause:** NEW SDK not installed

**Fix:**
```bash
pip install google-genai
```

---

### ❌ "WebSocket closes immediately"

**Cause:** Invalid session ID

**Fix:** Create a valid session first via REST API

---

### ❌ "Live API connection failed"

**Possible Causes:**
1. Invalid GEMINI_API_KEY
2. Python version < 3.9
3. google-genai not installed
4. Network/firewall issues

**Fix:** Check `INSTALLATION.md` for troubleshooting

---

## Summary

You've learned how to test:

✅ REST API endpoints (7 endpoints)
✅ WebSocket connections
✅ Text messaging
✅ Error handling
✅ Integration flows
✅ Database persistence

**Next Steps:**
- Implement audio capture on client
- Build full frontend application
- Deploy to production

**Need Help?**
- See `INSTALLATION.md` for setup issues
- See `README.md` for API documentation
- See `QUICK_START.md` for running the project

---

**Happy Testing! 🚀**

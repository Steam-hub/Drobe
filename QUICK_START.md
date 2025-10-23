# Quick Start Guide - Audio Chat API

This guide will help you get the Audio Chat API running in **5 simple steps**.

---

## Prerequisites Check ✅

Before starting, verify you have:

- [ ] **Python 3.9 or higher** (CRITICAL - check with `python --version`)
- [ ] **pip** package manager
- [ ] **Git** (to clone/pull code)
- [ ] **Gemini API Key** from [Google AI Studio](https://aistudio.google.com/app/apikey)
- [ ] **Text editor** (VS Code, PyCharm, etc.)

---

## Step 1: Check Python Version ⚠️

**This is the MOST IMPORTANT step!**

```bash
# Check Python version
python --version

# MUST show: Python 3.9.x or higher (3.10, 3.11, 3.12, etc.)
```

**If you see Python 3.8 or lower:**
- ❌ **STOP** - The Live API will NOT work
- ✅ Follow the upgrade guide in `INSTALLATION.md`
- Then come back here

---

## Step 2: Install Dependencies

```bash
# Navigate to project directory
cd C:\Users\OSAMA\SteamHubGame\Drobe

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate

# Linux/Mac:
# source venv/bin/activate

# Install NEW Gemini SDK (IMPORTANT)
pip install google-genai

# Install other dependencies
pip install django==4.2.7 djangorestframework django-cors-headers channels daphne pillow python-dotenv websockets

# Verify google-genai SDK installed correctly
python -c "from google import genai; print('✅ SDK installed correctly')"
```

**Expected Output:**
```
✅ SDK installed correctly
```

**If you see an error:**
- Check Python version again (must be 3.9+)
- Try: `pip install --upgrade google-genai`

---

## Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Windows:
copy .env.example .env

# Linux/Mac:
# cp .env.example .env
```

Edit `.env` and add your API key:

```env
# REQUIRED: Your Gemini API Key
GEMINI_API_KEY=your_actual_api_key_here

# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Get your API Key:**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key
4. Paste it into `.env`

---

## Step 4: Setup Database

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Expected output:
# Running migrations:
#   Applying audio_chat.0001_initial... OK
#   Applying audio_chat.0002_... OK

# Create admin user (optional but recommended)
python manage.py createsuperuser
# Follow prompts to set username, email, password
```

---

## Step 5: Start the Server 🚀

```bash
# Start Django development server
python manage.py runserver

# Expected output:
# Watching for file changes with StatReloader
# Performing system checks...
# System check identified no issues (0 silenced).
# January 15, 2025 - 10:30:00
# Django version 4.2.7, using settings 'Drobe.settings'
# Starting ASGI/Daphne development server at http://127.0.0.1:8000/
# Quit the server with CTRL-BREAK.
```

**Server is running!** ✅

---

## Verify Installation ✅

### Test 1: Health Check

Open browser or use curl:

```bash
curl http://localhost:8000/api/health/

# Expected response:
# {"status":"ok","message":"Audio Chat API is running"}
```

### Test 2: Admin Panel

1. Go to: http://localhost:8000/admin/
2. Login with superuser credentials
3. You should see "Audio Chat" app with ChatSessions and ChatMessages

### Test 3: Create a Session

```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d "{\"level_description\": \"Test level\", \"child_age\": 7}"

# Expected response:
# {
#     "id": "some-uuid-here",
#     "level_description": "Test level",
#     "child_age": 7,
#     "created_at": "2025-01-15T10:30:00Z",
#     "is_active": true
# }
```

**Save the `id` from the response - you'll need it for WebSocket testing!**

---

## Common Issues and Quick Fixes

### Issue 1: "No module named 'google.genai'"

**Solution:**
```bash
pip install google-genai
```

### Issue 2: "google-genai requires Python 3.9+"

**Solution:**
- Your Python version is too old
- See `INSTALLATION.md` for upgrade instructions

### Issue 3: "GEMINI_API_KEY is not configured"

**Solution:**
- Check `.env` file exists
- Verify `GEMINI_API_KEY=...` is set correctly
- No spaces around the `=` sign
- No quotes around the key

### Issue 4: "Address already in use"

**Solution:**
```bash
# Something is using port 8000
# Try a different port:
python manage.py runserver 8001
```

### Issue 5: Server starts but WebSocket doesn't work

**Solution:**
- Make sure `channels` is installed: `pip install channels`
- Check `INSTALLED_APPS` in settings.py includes 'channels'
- Verify `daphne` is listed first in `INSTALLED_APPS`

---

## Next Steps

Now that the server is running, you can:

1. **Test REST API:**
   - Import `Audio_Chat_API.postman_collection.json` into Postman
   - Test all endpoints

2. **Test WebSocket:**
   - See `TESTING_GUIDE.md` for detailed examples
   - Use browser console or WebSocket client

3. **Implement Client:**
   - Build frontend with audio capture
   - See client examples in `INSTALLATION.md`

---

## Quick Command Reference

```bash
# Start server
python manage.py runserver

# Stop server
# Press Ctrl+C

# Create new migration (after model changes)
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Django shell (for debugging)
python manage.py shell

# Check for issues
python manage.py check

# Collect static files (production)
python manage.py collectstatic
```

---

## Development URLs

| Service | URL |
|---------|-----|
| API Base | http://localhost:8000/api/ |
| Admin Panel | http://localhost:8000/admin/ |
| Health Check | http://localhost:8000/api/health/ |
| WebSocket | ws://localhost:8000/ws/audio-chat/{session_id}/ |

---

## Project Structure Quick Reference

```
Drobe/
├── audio_chat/                  # Main app
│   ├── services/
│   │   └── gemini_live_service.py  # Live API service
│   ├── consumers.py             # WebSocket handler
│   ├── views.py                 # REST API endpoints
│   └── models.py                # Database models
├── Drobe/
│   ├── settings.py              # Configuration
│   └── asgi.py                  # WebSocket config
├── .env                         # Environment variables (CREATE THIS)
├── manage.py                    # Django management
└── QUICK_START.md              # This file
```

---

## Summary

✅ **You should now have:**
1. Python 3.9+ verified
2. Dependencies installed (including google-genai)
3. Environment variables configured
4. Database migrated
5. Server running on http://localhost:8000

✅ **You can now:**
- Access the API at http://localhost:8000/api/
- Test with Postman using the collection
- Connect via WebSocket for audio streaming
- Manage data via Admin panel

---

## Need Help?

- **Installation Issues:** See `INSTALLATION.md`
- **Testing:** See `TESTING_GUIDE.md`
- **API Details:** See `README.md`
- **Migration Info:** See `LIVE_API_MIGRATION_COMPLETE.md`

**Ready to test? See `TESTING_GUIDE.md` for detailed testing instructions!** 🚀

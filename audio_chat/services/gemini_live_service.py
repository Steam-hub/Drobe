"""
Gemini Live API Service using NEW google-genai SDK
Requires: Python 3.9+ and google-genai package

Install:
    pip install google-genai

Usage:
    from audio_chat.services.gemini_live_service import GeminiLiveService
"""
import asyncio
import io
import logging
from typing import Optional, Dict, Any, List, AsyncIterator
from django.conf import settings
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class GeminiLiveService:
    """
    Service class for Gemini Live API with native audio streaming
    Uses the NEW google-genai SDK (requires Python 3.9+)
    """

    def __init__(
        self,
        session_id: str,
        level_description: str,
        child_age: int = 7,
        history: Optional[List[Dict]] = None,
        initial_message: Optional[str] = None
    ):
        self.session_id = session_id
        self.level_description = level_description
        self.child_age = child_age
        self.api_key = settings.GEMINI_API_KEY
        self.initial_message = initial_message

        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not configured in settings")

        # Create client with proper http_options for Live API
        self.client = genai.Client(
            api_key=self.api_key,
            http_options={"api_version": "v1beta"}
        )

        # Use native audio model
        self.model = "models/gemini-2.5-flash-native-audio-preview-09-2025"

        # Build system instructions
        self.system_instruction = self._build_system_instruction()

        # Store history
        self.history = history or []

        # Live session (will be set when connection is established)
        self.live_session = None
        self.audio_queue = asyncio.Queue()

    def _build_system_instruction(self) -> str:
        """Build child-friendly system instructions"""
        return f"""You are a friendly, helpful AI assistant for children aged {self.child_age} years old.

Your role:
- Speak in simple, easy-to-understand language for {self.child_age}-year-olds
- Be patient, positive, and encouraging
- Use a warm, friendly tone like a helpful older sibling
- Keep explanations short and clear
- Celebrate their efforts and progress
- Give gentle hints rather than direct answers
- Make learning fun and engaging

Current Game Level: {self.level_description}

Guidelines:
- Never use complex vocabulary or technical terms
- Break down problems into simple steps
- Use examples children can relate to
- Always be supportive and never critical
- Keep responses concise
- Use an enthusiastic but not overly energetic tone

Remember: Help them learn and succeed while having fun!"""

    def _create_config(self) -> types.LiveConnectConfig:
        """Create Live API configuration matching Google's example"""
        config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=self.system_instruction,
            # Media resolution for better audio quality
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Kore"  # Changed to Kore voice
                    )
                )
            ),
            # Context window compression to handle long conversations
            context_window_compression=types.ContextWindowCompressionConfig(
                trigger_tokens=25600,
                sliding_window=types.SlidingWindow(target_tokens=12800),
            ),
        )
        return config

    async def start_live_session(self):
        """
        Start a Live API session for real-time audio streaming
        NOTE: This should be called within an async context manager
        """
        if self.live_session:
            logger.warning("Live session already exists")
            return

        try:
            config = self._create_config()

            # This returns an async context manager - store it for use in connect()
            self._connection_context = self.client.aio.live.connect(
                model=self.model,
                config=config
            )

            # Enter the context manager
            self.live_session = await self._connection_context.__aenter__()
            logger.info(f"✅ Live session started for {self.session_id}")

            # Send initial message if provided (for context setting)
            if self.initial_message:
                logger.info(f"📤 Sending initial context message to Gemini")
                await self.live_session.send(
                    input=self.initial_message,
                    end_of_turn=True
                )
                logger.info(f"✅ Initial message sent: {self.initial_message[:50]}...")

        except Exception as e:
            logger.error(f"❌ Failed to start Live session: {str(e)}")
            raise

    async def close_session(self):
        """Close the Live API session"""
        if self.live_session:
            try:
                # Properly exit the async context manager
                if hasattr(self, '_connection_context'):
                    await self._connection_context.__aexit__(None, None, None)
                    self._connection_context = None
                self.live_session = None
                logger.info(f"Live session closed for {self.session_id}")
            except Exception as e:
                logger.error(f"Error closing Live session: {str(e)}")

    async def send_audio(self, audio_bytes: bytes) -> Dict[str, Any]:
        """
        Send audio data to Gemini Live API

        Args:
            audio_bytes: PCM audio data (16-bit, 16kHz, mono)

        Returns:
            Success status
        """
        try:
            if not self.live_session:
                logger.error("Cannot send audio: Live session not started")
                return {
                    "success": False,
                    "error": "Live session not started",
                    "session_id": self.session_id
                }

            # Send audio in the format expected by Live API
            # According to Google's example: {"data": audio_bytes, "mime_type": "audio/pcm"}
            # CRITICAL: Gemini expects continuous audio stream, it detects end-of-speech automatically
            await self.live_session.send(
                input={"data": audio_bytes, "mime_type": "audio/pcm"}
            )

            logger.debug(f"Sent audio chunk: {len(audio_bytes)} bytes (format: 16kHz PCM)")

            return {
                "success": True,
                "session_id": self.session_id
            }

        except Exception as e:
            logger.error(f"Error sending audio: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }

    async def send_text(self, text: str, end_of_turn: bool = True) -> Dict[str, Any]:
        """
        Send text message via Live API

        Args:
            text: Text message from child
            end_of_turn: Whether to signal end of turn

        Returns:
            Success status
        """
        try:
            if not self.live_session:
                return {
                    "success": False,
                    "error": "Live session not started",
                    "session_id": self.session_id
                }

            # Send text message
            await self.live_session.send(
                input=text,
                end_of_turn=end_of_turn
            )

            logger.info(f"Sent text message, end_of_turn={end_of_turn}")

            return {
                "success": True,
                "session_id": self.session_id
            }

        except Exception as e:
            logger.error(f"Error sending text: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }

    async def signal_end_of_turn(self) -> Dict[str, Any]:
        """
        Signal end of turn to Gemini (e.g., when user stops speaking)
        This tells Gemini to start generating a response

        Returns:
            Success status
        """
        try:
            if not self.live_session:
                return {
                    "success": False,
                    "error": "Live session not started",
                    "session_id": self.session_id
                }

            # Send empty message with end_of_turn to trigger response
            await self.live_session.send(
                input="",
                end_of_turn=True
            )

            logger.info(f"🛑 Signaled end of turn to Gemini")

            return {
                "success": True,
                "session_id": self.session_id
            }

        except Exception as e:
            logger.error(f"Error signaling end of turn: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }

    async def receive_responses(self) -> AsyncIterator[Dict[str, Any]]:
        """
        Receive responses from Gemini Live API using turn-based pattern
        This is a generator that yields audio/text chunks

        CRITICAL: After each turn completes, yields a turn_complete event
        to allow clearing of audio buffers (prevents overlapping audio)

        Yields:
            Dict with response data (audio, text, or turn_complete)
        """
        if not self.live_session:
            logger.error("Cannot receive responses: Live session not started")
            return

        try:
            logger.info(f"🎧 Starting to listen for responses from Gemini for session {self.session_id}")
            while True:
                # Get a turn from the session (this is the correct pattern from Google's example)
                logger.debug(f"Waiting for new turn from Gemini...")
                turn = self.live_session.receive()

                turn_audio_chunks = 0
                turn_text_chunks = 0

                async for response in turn:
                    # Audio response (binary PCM data at 24kHz)
                    if data := response.data:
                        turn_audio_chunks += 1
                        logger.debug(f"Received audio chunk #{turn_audio_chunks}: {len(data)} bytes")
                        yield {
                            "type": "audio",
                            "data": data,  # Audio bytes (24kHz PCM)
                            "session_id": self.session_id
                        }

                    # Text response (if modality includes TEXT)
                    if text := response.text:
                        turn_text_chunks += 1
                        logger.debug(f"Received text chunk #{turn_text_chunks}: {text}")
                        yield {
                            "type": "text",
                            "content": text,
                            "session_id": self.session_id
                        }

                    # Tool calls (if using function calling)
                    if hasattr(response, 'tool_call') and response.tool_call:
                        yield {
                            "type": "tool_call",
                            "tool_call": response.tool_call,
                            "session_id": self.session_id
                        }

                # Turn is complete - signal to clear audio buffers
                # This is CRITICAL to prevent overlapping audio from multiple responses
                logger.info(f"✅ Turn complete for session {self.session_id} - Audio: {turn_audio_chunks}, Text: {turn_text_chunks}")
                yield {
                    "type": "turn_complete",
                    "session_id": self.session_id
                }

        except asyncio.CancelledError:
            logger.info("Response receiving cancelled")
            raise
        except Exception as e:
            logger.error(f"❌ Error receiving responses: {str(e)}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "session_id": self.session_id
            }

    async def send_image(self, image_bytes: bytes, mime_type: str = "image/png", question: Optional[str] = None) -> Dict[str, Any]:
        """
        Send image to Live API

        Args:
            image_bytes: Image data
            mime_type: Image MIME type
            question: Optional question about the image

        Returns:
            Success status
        """
        try:
            if not self.live_session:
                await self.start_live_session()

            # Prepare image blob
            image_blob = types.Blob(
                data=image_bytes,
                mime_type=mime_type
            )

            # Send with optional question
            if question:
                await self.live_session.send(
                    input=[question, image_blob],
                    end_of_turn=True
                )
            else:
                await self.live_session.send(
                    input=[
                        "Can you help me understand what's happening in this screenshot? I'm having trouble with this part of the game.",
                        image_blob
                    ],
                    end_of_turn=True
                )

            return {
                "success": True,
                "session_id": self.session_id
            }

        except Exception as e:
            logger.error(f"Error sending image: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "session_id": self.session_id
            }

    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get conversation history

        Returns:
            List of messages
        """
        return self.history

    async def __aenter__(self):
        """Context manager entry"""
        await self.start_live_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        await self.close_session()

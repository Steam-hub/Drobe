"""
WebSocket consumers for real-time audio streaming with Gemini Live API
Uses NEW google-genai SDK for bidirectional audio streaming
"""
import json
import logging
import base64
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatSession, ChatMessage
from .services.gemini_live_service import GeminiLiveService

logger = logging.getLogger(__name__)


class AudioChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time audio chat with Gemini
    """

    async def connect(self):
        """
        Handle WebSocket connection with Live API and chat history
        """
        # Get session_id from URL route
        self.session_id = self.scope['url_route']['kwargs']['session_id']

        # Validate session exists
        self.session = await self.get_session(self.session_id)

        if not self.session:
            await self.close(code=4004)
            return

        # Load chat history from database
        chat_history = await self.load_chat_history()

        # Get initial message from session (if provided)
        initial_message = self.session.initial_message

        # Initialize Gemini Live API service with history
        self.gemini_live_service = GeminiLiveService(
            session_id=str(self.session.id),
            level_description=self.session.level_description,
            child_age=self.session.child_age,
            history=chat_history,  # Pass existing history
            initial_message=initial_message  # Pass initial context from session
        )

        # Accept the connection
        await self.accept()

        try:
            # Start Live API session
            await self.gemini_live_service.start_live_session()

            # Start background task to listen for responses from Gemini
            self.response_task = asyncio.create_task(self.listen_for_gemini_responses())

            # Send welcome message with history count
            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Connected to Gemini Live API with native audio streaming',
                'session_id': str(self.session.id),
                'history_message_count': len(chat_history),
                'model': 'gemini-2.5-flash-native-audio-preview-09-2025',
                'audio_format': 'PCM 16kHz 16-bit mono (input), 24kHz mono (output)'
            }))

            logger.info(f"✅ Live API session started for {self.session_id} with {len(chat_history)} historical messages")

        except Exception as e:
            logger.error(f"❌ Failed to start Live API session: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to connect to Gemini Live API',
                'error': str(e),
                'note': 'Live API requires Python 3.9+ and google-genai package'
            }))
            await self.close(code=4011)

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection and cleanup
        """
        # Cancel response listening task
        if hasattr(self, 'response_task') and not self.response_task.done():
            self.response_task.cancel()
            try:
                await self.response_task
            except asyncio.CancelledError:
                pass

        # Close Live API session
        if hasattr(self, 'gemini_live_service'):
            await self.gemini_live_service.close_session()

        logger.info(f"WebSocket disconnected for session {self.session_id} with code {close_code}")

    async def listen_for_gemini_responses(self):
        """
        Background task that continuously listens for responses from Gemini Live API
        and forwards them to the WebSocket client
        """
        try:
            async for response in self.gemini_live_service.receive_responses():
                if response['type'] == 'audio':
                    # Send audio data as binary to client
                    # Audio is 24kHz PCM from Gemini
                    await self.send(bytes_data=response['data'])
                    logger.debug(f"Sent audio chunk to client, size: {len(response['data'])} bytes")

                elif response['type'] == 'text':
                    # Send text response (if modality includes TEXT)
                    await self.save_message(
                        sender='assistant',
                        message_type='text',
                        text_content=response['content']
                    )
                    await self.send(text_data=json.dumps({
                        'type': 'response',
                        'content': response['content'],
                        'session_id': str(self.session.id)
                    }))
                    logger.info(f"Sent text response to client")

                elif response['type'] == 'turn_complete':
                    # Signal to client that turn is complete
                    # Client should clear its audio buffer to prevent overlapping audio
                    await self.send(text_data=json.dumps({
                        'type': 'turn_complete',
                        'session_id': str(self.session.id)
                    }))
                    logger.debug(f"Sent turn_complete signal to client")

                elif response['type'] == 'error':
                    # Handle errors from Live API
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Error from Gemini Live API',
                        'error': response['error']
                    }))
                    logger.error(f"Live API error: {response['error']}")

        except asyncio.CancelledError:
            logger.info("Response listening task cancelled")
        except Exception as e:
            logger.error(f"Error in response listening task: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error listening for responses',
                'error': str(e)
            }))

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming messages from WebSocket
        Supports both text and binary (audio) data
        """
        try:
            if text_data:
                # Handle text messages
                await self.handle_text_message(text_data)
            elif bytes_data:
                # Handle binary audio data
                await self.handle_audio_message(bytes_data)

        except Exception as e:
            logger.error(f"Error receiving message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error processing message',
                'error': str(e)
            }))

    async def handle_text_message(self, text_data):
        """
        Handle text messages (JSON format) and send via Live API
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'text')

            if message_type == 'text':
                # Handle text input from child
                text_content = data.get('content', '')

                if not text_content:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Text content is required'
                    }))
                    return

                # Save the child's message
                await self.save_message(
                    sender='child',
                    message_type='text',
                    text_content=text_content
                )

                # Send text to Live API (response will come via listen_for_gemini_responses)
                result = await self.gemini_live_service.send_text(text_content)

                if not result['success']:
                    await self.send(text_data=json.dumps({
                        'type': 'error',
                        'message': 'Failed to send text to Live API',
                        'error': result.get('error', 'Unknown error')
                    }))

                # Note: AI response will be received via the background listening task
                # and automatically sent back to the client

            elif message_type == 'audio_base64':
                # Handle audio data sent as base64 in JSON
                audio_base64 = data.get('content', '')
                if audio_base64:
                    audio_bytes = base64.b64decode(audio_base64)
                    await self.process_audio_data(audio_bytes)

            # NOTE: end_of_turn is NOT needed for audio streams!
            # Gemini Live API automatically detects end of speech using built-in VAD
            # Only use end_of_turn=True for TEXT messages
            # elif message_type == 'end_of_turn':
            #     logger.info("🛑 End of turn signal received from client")
            #     result = await self.gemini_live_service.signal_end_of_turn()
            #     if not result['success']:
            #         await self.send(text_data=json.dumps({
            #             'type': 'error',
            #             'message': 'Failed to signal end of turn',
            #             'error': result.get('error', 'Unknown error')
            #         }))

            elif message_type == 'ping':
                # Handle ping/keepalive
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error handling text message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error processing text message',
                'error': str(e)
            }))

    async def handle_audio_message(self, bytes_data):
        """
        Handle binary audio messages
        """
        try:
            await self.process_audio_data(bytes_data)

        except Exception as e:
            logger.error(f"Error handling audio message: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error processing audio message',
                'error': str(e)
            }))

    async def process_audio_data(self, audio_bytes):
        """
        Process audio data and send to Live API
        Audio should be: 16-bit PCM, 16kHz, mono
        """
        try:
            # Log audio received from client
            logger.debug(f"📥 Received audio from client: {len(audio_bytes)} bytes")

            # Send audio to Live API (response will come via listen_for_gemini_responses)
            result = await self.gemini_live_service.send_audio(audio_bytes)

            if not result['success']:
                logger.error(f"Failed to send audio to Live API: {result.get('error')}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Failed to send audio to Live API',
                    'error': result.get('error', 'Unknown error')
                }))

            # Note: AI audio response will be received via the background listening task
            # and automatically sent back to the client as binary audio (24kHz PCM)

        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}", exc_info=True)
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Failed to process audio',
                'error': str(e)
            }))

    @database_sync_to_async
    def get_session(self, session_id):
        """
        Get chat session from database
        """
        try:
            return ChatSession.objects.get(id=session_id, is_active=True)
        except ChatSession.DoesNotExist:
            return None

    @database_sync_to_async
    def load_chat_history(self):
        """
        Load chat history from database and format for Gemini
        Returns list of dicts with 'role' and 'parts' matching Gemini's Content format
        """
        messages = ChatMessage.objects.filter(session=self.session).order_by('created_at')

        history = []
        for msg in messages:
            # Map our sender types to Gemini's role types
            role = 'user' if msg.sender == 'child' else 'model'

            # Only include text messages in history for now
            if msg.text_content:
                history.append({
                    'role': role,
                    'parts': [{'text': msg.text_content}]
                })

        return history

    @database_sync_to_async
    def save_message(self, sender, message_type, text_content=None, audio_file=None):
        """
        Save message to database
        """
        return ChatMessage.objects.create(
            session=self.session,
            sender=sender,
            message_type=message_type,
            text_content=text_content,
            audio_file=audio_file
        )

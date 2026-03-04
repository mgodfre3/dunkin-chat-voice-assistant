import asyncio
import base64
import io
import json
import logging
import os
import struct
import time
from typing import Any

import aiohttp
import ssl

from aiohttp import web

from order_state import SessionIdentifiers, order_state_singleton
from rtmt import Tool, ToolResult, ToolResultDirection

logger = logging.getLogger("coffee-chat")

__all__ = ["RTLocalPipeline"]

# ---------------------------------------------------------------------------
# Service URLs (overridable via env vars)
# ---------------------------------------------------------------------------
WHISPER_STT_URL = os.environ.get("WHISPER_STT_URL", "http://whisper-stt.dunkin-voice.svc:8000")
FOUNDRY_LLM_URL = os.environ.get("FOUNDRY_LLM_URL", "http://phi-4-mini-gpu.foundry-local-operator.svc:5000")
FOUNDRY_API_KEY = os.environ.get("FOUNDRY_API_KEY", "")
PIPER_TTS_URL = os.environ.get("PIPER_TTS_URL", "http://piper-tts.dunkin-voice.svc:5000")
TTS_VOICE = os.environ.get("TTS_VOICE", "en_US-amy-medium")

# Audio constants
SAMPLE_RATE = 24000
BITS_PER_SAMPLE = 16
CHANNELS = 1
AUDIO_CHUNK_SIZE = 4800  # bytes per streaming chunk

# VAD constants
SPEECH_THRESHOLD = 500000
SILENCE_DURATION = 0.5  # seconds of silence before processing

LLM_MODEL = "Phi-4-mini-instruct-cuda-gpu:5"


# ---------------------------------------------------------------------------
# Audio helpers
# ---------------------------------------------------------------------------

def create_wav_header(pcm_data_len: int, sample_rate: int = SAMPLE_RATE,
                      bits_per_sample: int = BITS_PER_SAMPLE, channels: int = CHANNELS) -> bytes:
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    header = struct.pack(
        '<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + pcm_data_len, b'WAVE',
        b'fmt ', 16, 1, channels, sample_rate, byte_rate, block_align, bits_per_sample,
        b'data', pcm_data_len,
    )
    return header


def calculate_energy(pcm_bytes: bytes) -> float:
    if len(pcm_bytes) < 2:
        return 0.0
    n_samples = len(pcm_bytes) // 2
    samples = struct.unpack(f'<{n_samples}h', pcm_bytes[:n_samples * 2])
    return sum(s * s for s in samples) / len(samples)


def pcm_to_wav(pcm_data: bytes) -> bytes:
    return create_wav_header(len(pcm_data)) + pcm_data


def wav_to_pcm(wav_data: bytes) -> bytes:
    """Strip WAV header and return raw PCM data."""
    if wav_data[:4] == b'RIFF':
        # Find 'data' sub-chunk
        idx = wav_data.find(b'data')
        if idx != -1:
            # 4 bytes 'data' + 4 bytes chunk size
            data_size = struct.unpack_from('<I', wav_data, idx + 4)[0]
            return wav_data[idx + 8: idx + 8 + data_size]
    return wav_data


# ---------------------------------------------------------------------------
# Per-connection session state
# ---------------------------------------------------------------------------

class _ConnectionState:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.audio_buffer = bytearray()
        self.conversation: list[dict[str, Any]] = []
        self.speech_started = False
        self.last_speech_time: float = 0.0
        self.greeting_sent = False


# ---------------------------------------------------------------------------
# RTLocalPipeline – drop-in replacement for RTMiddleTier
# ---------------------------------------------------------------------------

class RTLocalPipeline:
    tools: dict[str, Tool]
    system_message: str | None = None
    temperature: float | None = None
    voice_choice: str | None = None

    def __init__(self, voice_choice: str | None = None):
        self.tools = {}
        self.voice_choice = voice_choice or TTS_VOICE
        if voice_choice is not None:
            logger.info("Local pipeline voice choice set to %s", voice_choice)

    # ------------------------------------------------------------------
    # Session-identifier helpers (mirrors RTMiddleTier)
    # ------------------------------------------------------------------

    @staticmethod
    async def _emit_session_identifiers(
        client_ws: web.WebSocketResponse,
        event_type: str,
        identifiers: SessionIdentifiers | None,
    ) -> None:
        if identifiers is None:
            return
        await client_ws.send_json({
            "type": event_type,
            "sessionToken": identifiers.session_token,
            "roundTripIndex": identifiers.round_trip_index,
            "roundTripToken": identifiers.round_trip_token,
        })

    # ------------------------------------------------------------------
    # Service calls
    # ------------------------------------------------------------------

    async def _stt(self, http: aiohttp.ClientSession, wav_bytes: bytes) -> str:
        """Send WAV audio to Whisper STT and return transcribed text."""
        form = aiohttp.FormData()
        form.add_field('file', wav_bytes, filename='audio.wav', content_type='audio/wav')
        form.add_field('model', 'whisper-1')
        form.add_field('language', 'en')
        async with http.post(f"{WHISPER_STT_URL}/v1/audio/transcriptions", data=form) as resp:
            resp.raise_for_status()
            result = await resp.json()
            return result.get("text", "")

    async def _llm_chat(self, http: aiohttp.ClientSession,
                        messages: list[dict], tools_schema: list[dict] | None = None) -> dict:
        """Call Phi-4 Mini chat completions endpoint."""
        payload: dict[str, Any] = {
            "model": LLM_MODEL,
            "messages": messages,
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if tools_schema:
            payload["tools"] = tools_schema
            payload["tool_choice"] = "auto"
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if FOUNDRY_API_KEY:
            headers["Authorization"] = f"Bearer {FOUNDRY_API_KEY}"
        async with http.post(f"{FOUNDRY_LLM_URL}/v1/chat/completions",
                             json=payload, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _tts(self, http: aiohttp.ClientSession, text: str) -> bytes:
        """Call Piper TTS and return WAV audio bytes."""
        payload = {
            "model": self.voice_choice or TTS_VOICE,
            "input": text,
            "response_format": "wav",
        }
        async with http.post(f"{PIPER_TTS_URL}/v1/audio/speech", json=payload) as resp:
            resp.raise_for_status()
            return await resp.read()

    # ------------------------------------------------------------------
    # Tool execution
    # ------------------------------------------------------------------

    def _build_tools_schema(self) -> list[dict]:
        return [tool.schema for tool in self.tools.values()]

    async def _execute_tool_calls(
        self,
        http: aiohttp.ClientSession,
        client_ws: web.WebSocketResponse,
        state: _ConnectionState,
        tool_calls: list[dict],
    ) -> str:
        """Execute tool calls, append results to conversation, re-call LLM
        for a final natural-language answer."""

        # Build assistant message with tool_calls
        assistant_msg: dict[str, Any] = {"role": "assistant", "tool_calls": tool_calls}
        state.conversation.append(assistant_msg)

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args_str = tc["function"]["arguments"]
            fn_args = json.loads(fn_args_str) if isinstance(fn_args_str, str) else fn_args_str
            tc_id = tc["id"]

            tool = self.tools.get(fn_name)
            if tool is None:
                tool_output = f"Unknown tool: {fn_name}"
                destination = ToolResultDirection.TO_SERVER
            else:
                if fn_name in ("update_order", "get_order"):
                    result: ToolResult = await tool.target(fn_args, state.session_id)
                else:
                    result = await tool.target(fn_args)
                tool_output = result.to_text()
                destination = result.destination

                if destination == ToolResultDirection.TO_CLIENT:
                    await client_ws.send_json({
                        "type": "extension.middle_tier_tool_response",
                        "tool_name": fn_name,
                        "tool_result": tool_output,
                    })

            state.conversation.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": tool_output if destination == ToolResultDirection.TO_SERVER else "",
            })

        # Re-call LLM with tool results for final response
        llm_resp = await self._llm_chat(http, state.conversation, self._build_tools_schema())
        choice = llm_resp["choices"][0]
        msg = choice["message"]

        # Handle nested tool calls (up to 3 levels)
        if msg.get("tool_calls"):
            return await self._execute_tool_calls(http, client_ws, state, msg["tool_calls"])

        final_text = msg.get("content", "")
        state.conversation.append({"role": "assistant", "content": final_text})
        return final_text

    # ------------------------------------------------------------------
    # Audio streaming helpers
    # ------------------------------------------------------------------

    async def _stream_audio_response(
        self,
        http: aiohttp.ClientSession,
        client_ws: web.WebSocketResponse,
        state: _ConnectionState,
        text: str,
    ) -> None:
        """TTS the text, then stream audio + transcript to the client,
        finishing with response.done."""

        # Send transcript delta
        if text:
            await client_ws.send_json({
                "type": "response.audio_transcript.delta",
                "delta": text,
            })

        # Get TTS audio
        try:
            wav_bytes = await self._tts(http, text)
            pcm_data = wav_to_pcm(wav_bytes)
        except Exception as exc:
            logger.error("TTS failed: %s", exc)
            pcm_data = b""

        # Stream audio chunks
        offset = 0
        while offset < len(pcm_data):
            chunk = pcm_data[offset: offset + AUDIO_CHUNK_SIZE]
            b64 = base64.b64encode(chunk).decode("ascii")
            await client_ws.send_json({
                "type": "response.audio.delta",
                "delta": b64,
            })
            offset += AUDIO_CHUNK_SIZE

        # Send response.done
        await client_ws.send_json({
            "type": "response.done",
            "response": {"output": []},
        })

        # Advance round-trip tracking
        identifiers = order_state_singleton.advance_round_trip(state.session_id)
        await self._emit_session_identifiers(client_ws, "extension.round_trip_token", identifiers)

    # ------------------------------------------------------------------
    # Full speech processing pipeline
    # ------------------------------------------------------------------

    async def _process_speech(
        self,
        http: aiohttp.ClientSession,
        client_ws: web.WebSocketResponse,
        state: _ConnectionState,
    ) -> None:
        pcm_data = bytes(state.audio_buffer)
        state.audio_buffer.clear()

        if not pcm_data:
            return

        # 1. STT
        wav_bytes = pcm_to_wav(pcm_data)
        try:
            transcript = await self._stt(http, wav_bytes)
        except Exception as exc:
            logger.error("STT failed: %s", exc)
            transcript = ""

        if not transcript.strip():
            logger.info("Empty transcript, skipping LLM call")
            return

        logger.info("STT transcript: %s", transcript)

        # Notify client of completed transcription
        await client_ws.send_json({
            "type": "conversation.item.input_audio_transcription.completed",
            "transcript": transcript,
        })

        # 2. LLM
        state.conversation.append({"role": "user", "content": transcript})

        tools_schema = self._build_tools_schema()
        try:
            llm_resp = await self._llm_chat(http, state.conversation, tools_schema or None)
        except Exception as exc:
            logger.error("LLM call failed: %s", exc)
            await client_ws.send_json({"type": "error", "error": {"message": str(exc)}})
            return

        choice = llm_resp["choices"][0]
        msg = choice["message"]

        # 3. Handle tool calls or direct text
        if msg.get("tool_calls"):
            try:
                final_text = await self._execute_tool_calls(http, client_ws, state, msg["tool_calls"])
            except Exception as exc:
                logger.error("Tool execution failed: %s", exc)
                final_text = "I'm sorry, something went wrong while processing your request."
                state.conversation.append({"role": "assistant", "content": final_text})
        else:
            final_text = msg.get("content", "")
            state.conversation.append({"role": "assistant", "content": final_text})

        # 4. TTS + stream
        await self._stream_audio_response(http, client_ws, state, final_text)

    # ------------------------------------------------------------------
    # Auto-greeting
    # ------------------------------------------------------------------

    async def _send_greeting(
        self,
        http: aiohttp.ClientSession,
        client_ws: web.WebSocketResponse,
        state: _ConnectionState,
    ) -> None:
        state.conversation.append({
            "role": "user",
            "content": "Please greet the guest with: 'Welcome to Dunkin! How may I help you today?'",
        })
        try:
            llm_resp = await self._llm_chat(http, state.conversation)
            greeting = llm_resp["choices"][0]["message"].get("content", "Welcome to Dunkin! How may I help you today?")
        except Exception as exc:
            logger.error("Greeting LLM call failed: %s", exc)
            greeting = "Welcome to Dunkin! How may I help you today?"

        state.conversation.append({"role": "assistant", "content": greeting})
        await self._stream_audio_response(http, client_ws, state, greeting)
        state.greeting_sent = True

    # ------------------------------------------------------------------
    # VAD + audio buffering
    # ------------------------------------------------------------------

    async def _handle_audio_append(
        self,
        http: aiohttp.ClientSession,
        client_ws: web.WebSocketResponse,
        state: _ConnectionState,
        audio_b64: str,
    ) -> None:
        pcm_chunk = base64.b64decode(audio_b64)
        energy = calculate_energy(pcm_chunk)

        if energy > SPEECH_THRESHOLD:
            if not state.speech_started:
                state.speech_started = True
                await client_ws.send_json({"type": "input_audio_buffer.speech_started"})
            state.last_speech_time = time.monotonic()
            state.audio_buffer.extend(pcm_chunk)
        elif state.speech_started:
            state.audio_buffer.extend(pcm_chunk)
            if time.monotonic() - state.last_speech_time >= SILENCE_DURATION:
                # Silence detected — process buffered speech
                state.speech_started = False
                await self._process_speech(http, client_ws, state)

    # ------------------------------------------------------------------
    # WebSocket handler
    # ------------------------------------------------------------------

    async def _websocket_handler(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        session_id = order_state_singleton.create_session()
        state = _ConnectionState(session_id)

        # Initialise conversation with system prompt
        if self.system_message:
            state.conversation.append({"role": "system", "content": self.system_message})

        # Allow self-signed certs from Foundry Local operator
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)

        async with aiohttp.ClientSession(connector=connector) as http:
            # Send session.created
            await ws.send_json({
                "type": "session.created",
                "session": {
                    "id": session_id,
                    "voice": self.voice_choice,
                    "instructions": "",
                    "tools": [],
                    "tool_choice": "none",
                    "max_response_output_tokens": None,
                },
            })

            # Emit session metadata
            identifiers = order_state_singleton.get_session_identifiers(session_id)
            await self._emit_session_identifiers(ws, "extension.session_metadata", identifiers)

            try:
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        msg_type = data.get("type")

                        if msg_type == "session.update":
                            # Send greeting on first session.update (client is ready)
                            if not state.greeting_sent:
                                await self._send_greeting(http, ws, state)

                        elif msg_type == "input_audio_buffer.append":
                            if not state.greeting_sent:
                                await self._send_greeting(http, ws, state)
                            audio_b64 = data.get("audio", "")
                            if audio_b64:
                                await self._handle_audio_append(http, ws, state, audio_b64)

                        elif msg_type == "input_audio_buffer.clear":
                            state.audio_buffer.clear()
                            state.speech_started = False

                    elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                        break
            except ConnectionResetError:
                pass
            finally:
                order_state_singleton.delete_session(session_id)

        return ws

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def attach_to_app(self, app: web.Application, path: str) -> None:
        app.router.add_get(path, self._websocket_handler)

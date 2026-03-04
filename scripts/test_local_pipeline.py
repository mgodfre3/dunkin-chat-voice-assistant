#!/usr/bin/env python3
"""
End-to-end integration test for the Dunkin Chat Voice Assistant local pipeline.

Tests each service individually and then the full STT -> LLM -> TTS pipeline.

Environment variables:
  WHISPER_STT_URL  — Whisper STT base URL  (default: http://whisper-stt.dunkin-voice.svc:8000)
  FOUNDRY_LLM_URL  — Phi-4 Mini LLM base URL (default: https://phi-4-mini-gpu.foundry-local-operator.svc:5000)
  FOUNDRY_API_KEY   — Bearer token for LLM   (required)
  PIPER_TTS_URL    — Piper TTS base URL     (default: http://piper-tts.dunkin-voice.svc:5000)

Usage:
  # Inside the cluster (kubectl exec):
  python3 test_local_pipeline.py

  # With port-forwarding from outside:
  WHISPER_STT_URL=http://localhost:8000 \
  FOUNDRY_LLM_URL=https://localhost:5000 \
  FOUNDRY_API_KEY=my-key \
  PIPER_TTS_URL=http://localhost:5001 \
  python3 test_local_pipeline.py
"""

import io
import json
import math
import os
import ssl
import struct
import sys
import time
import urllib.error
import urllib.request
import wave


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

WHISPER_STT_URL = os.environ.get(
    "WHISPER_STT_URL", "http://whisper-stt.dunkin-voice.svc:8000"
)
FOUNDRY_LLM_URL = os.environ.get(
    "FOUNDRY_LLM_URL", "https://phi-4-mini-gpu.foundry-local-operator.svc:5000"
)
FOUNDRY_API_KEY = os.environ.get("FOUNDRY_API_KEY", "")
PIPER_TTS_URL = os.environ.get(
    "PIPER_TTS_URL", "http://piper-tts.dunkin-voice.svc:5000"
)

TIMEOUT_SECONDS = 30
LLM_TIMEOUT_SECONDS = 120  # LLM inference can be slow

# SSL context that skips certificate verification (Foundry uses self-signed certs)
_unverified_ssl = ssl.create_default_context()
_unverified_ssl.check_hostname = False
_unverified_ssl.verify_mode = ssl.CERT_NONE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class TestResult:
    def __init__(self, name: str):
        self.name = name
        self.passed = False
        self.duration = 0.0
        self.detail = ""
        self.error = ""


def generate_sine_wav(duration_s: float = 1.0, freq_hz: float = 440.0,
                      sample_rate: int = 16000) -> bytes:
    """Generate an in-memory WAV file containing a sine wave."""
    num_samples = int(sample_rate * duration_s)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        samples = bytearray()
        for i in range(num_samples):
            value = int(32767 * 0.5 * math.sin(2 * math.pi * freq_hz * i / sample_rate))
            samples.extend(struct.pack("<h", value))
        wf.writeframes(bytes(samples))
    return buf.getvalue()


def build_multipart(fields: dict, files: dict, boundary: str) -> bytes:
    """Build a multipart/form-data body from fields and files."""
    lines = []
    for key, value in fields.items():
        lines.append(f"--{boundary}".encode())
        lines.append(f'Content-Disposition: form-data; name="{key}"'.encode())
        lines.append(b"")
        lines.append(value.encode() if isinstance(value, str) else value)
    for key, (filename, data, content_type) in files.items():
        lines.append(f"--{boundary}".encode())
        lines.append(
            f'Content-Disposition: form-data; name="{key}"; filename="{filename}"'.encode()
        )
        lines.append(f"Content-Type: {content_type}".encode())
        lines.append(b"")
        lines.append(data)
    lines.append(f"--{boundary}--".encode())
    lines.append(b"")
    return b"\r\n".join(lines)


def http_request(url: str, method: str = "GET", data: bytes = None,
                 headers: dict = None, timeout: int = TIMEOUT_SECONDS) -> tuple:
    """Perform an HTTP(S) request. Returns (status_code, headers, body_bytes)."""
    headers = headers or {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    ctx = _unverified_ssl if url.startswith("https://") else None
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def run_test(func) -> TestResult:
    """Execute a test function and capture timing / errors."""
    result = TestResult(func.__doc__ or func.__name__)
    start = time.time()
    try:
        func(result)
    except Exception as exc:
        result.error = str(exc)
    result.duration = time.time() - start
    return result


def print_banner(title: str):
    width = 60
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


def print_result(r: TestResult):
    status = "\033[32mPASS\033[0m" if r.passed else "\033[31mFAIL\033[0m"
    print(f"  [{status}] {r.name}  ({r.duration:.2f}s)")
    if r.detail:
        for line in r.detail.strip().splitlines():
            print(f"         {line}")
    if r.error:
        for line in r.error.strip().splitlines():
            print(f"         \033[31m{line}\033[0m")


# ---------------------------------------------------------------------------
# Individual service tests
# ---------------------------------------------------------------------------

def test_whisper_health(r: TestResult):
    """Whisper STT — health check"""
    status, _, body = http_request(f"{WHISPER_STT_URL}/health")
    r.detail = f"status={status} body={body[:200]}"
    r.passed = status == 200


def test_whisper_transcribe(r: TestResult):
    """Whisper STT — transcribe sine-wave WAV"""
    wav_data = generate_sine_wav(duration_s=1.0, freq_hz=440.0)
    boundary = "----TestBoundary7d3b4a2e"
    body = build_multipart(
        fields={"model": "whisper-1", "language": "en"},
        files={"file": ("test.wav", wav_data, "audio/wav")},
        boundary=boundary,
    )
    status, _, resp_body = http_request(
        f"{WHISPER_STT_URL}/v1/audio/transcriptions",
        method="POST",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    r.detail = f"status={status} response={resp_body[:300]}"
    # A 200 means the service processed the audio (even if transcript is empty for a tone)
    r.passed = status == 200


def test_llm_chat(r: TestResult):
    """Phi-4 Mini LLM — chat completion"""
    if not FOUNDRY_API_KEY:
        r.error = "FOUNDRY_API_KEY not set — skipping"
        return

    payload = json.dumps({
        "model": "Phi-4-mini-instruct-cuda-gpu:5",
        "messages": [
            {"role": "system", "content": "You are a helpful Dunkin' assistant."},
            {"role": "user", "content": "What are three popular drinks on the Dunkin menu?"},
        ],
        "max_tokens": 256,
        "temperature": 0.7,
    }).encode()

    status, _, resp_body = http_request(
        f"{FOUNDRY_LLM_URL}/v1/chat/completions",
        method="POST",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FOUNDRY_API_KEY}",
        },
        timeout=LLM_TIMEOUT_SECONDS,
    )
    try:
        resp_json = json.loads(resp_body)
        content = resp_json.get("choices", [{}])[0].get("message", {}).get("content", "")
        r.detail = f"status={status} content={content[:200]}"
    except (json.JSONDecodeError, KeyError):
        r.detail = f"status={status} raw={resp_body[:300]}"
    r.passed = status == 200


def test_piper_health(r: TestResult):
    """Piper TTS — health check (/docs)"""
    status, _, body = http_request(f"{PIPER_TTS_URL}/docs")
    r.detail = f"status={status} body_length={len(body)}"
    r.passed = status == 200


def test_piper_synthesize(r: TestResult):
    """Piper TTS — synthesize speech"""
    payload = json.dumps({
        "model": "en_US-amy-medium",
        "input": "Welcome to Dunkin. How can I help you today?",
        "response_format": "wav",
    }).encode()

    status, hdrs, resp_body = http_request(
        f"{PIPER_TTS_URL}/v1/audio/speech",
        method="POST",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    is_wav = resp_body[:4] == b"RIFF" and b"WAVE" in resp_body[:12]
    r.detail = (
        f"status={status} body_length={len(resp_body)} "
        f"content_type={hdrs.get('Content-Type', 'n/a')} is_wav={is_wav}"
    )
    r.passed = status == 200 and is_wav


# ---------------------------------------------------------------------------
# Full pipeline test: STT → LLM → TTS
# ---------------------------------------------------------------------------

def test_full_pipeline(r: TestResult):
    """Full pipeline — STT → LLM → TTS"""
    if not FOUNDRY_API_KEY:
        r.error = "FOUNDRY_API_KEY not set — skipping pipeline test"
        return

    details = []

    # --- Step 1: STT -------------------------------------------------------
    wav_data = generate_sine_wav(duration_s=1.0, freq_hz=440.0)
    boundary = "----PipelineBoundary9c8f1a3d"
    mp_body = build_multipart(
        fields={"model": "whisper-1", "language": "en"},
        files={"file": ("test.wav", wav_data, "audio/wav")},
        boundary=boundary,
    )
    stt_status, _, stt_body = http_request(
        f"{WHISPER_STT_URL}/v1/audio/transcriptions",
        method="POST",
        data=mp_body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    if stt_status != 200:
        r.error = f"STT failed: status={stt_status} body={stt_body[:200]}"
        return

    try:
        transcript = json.loads(stt_body).get("text", "").strip()
    except (json.JSONDecodeError, AttributeError):
        transcript = stt_body.decode(errors="replace").strip()

    # Use a fallback prompt when the sine wave produces no meaningful text
    user_text = transcript if transcript else "What iced coffee drinks do you have?"
    details.append(f"STT transcript: '{transcript}' (using: '{user_text}')")

    # --- Step 2: LLM -------------------------------------------------------
    llm_payload = json.dumps({
        "model": "Phi-4-mini-instruct-cuda-gpu:5",
        "messages": [
            {"role": "system", "content": "You are a helpful Dunkin' assistant. Keep answers brief."},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 256,
        "temperature": 0.7,
    }).encode()

    llm_status, _, llm_body = http_request(
        f"{FOUNDRY_LLM_URL}/v1/chat/completions",
        method="POST",
        data=llm_payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FOUNDRY_API_KEY}",
        },
        timeout=LLM_TIMEOUT_SECONDS,
    )
    if llm_status != 200:
        r.error = f"LLM failed: status={llm_status} body={llm_body[:200]}"
        return

    try:
        llm_text = json.loads(llm_body)["choices"][0]["message"]["content"]
    except (json.JSONDecodeError, KeyError, IndexError):
        r.error = f"LLM response parse error: {llm_body[:300]}"
        return

    details.append(f"LLM response: '{llm_text[:120]}...'")

    # --- Step 3: TTS -------------------------------------------------------
    tts_payload = json.dumps({
        "model": "en_US-amy-medium",
        "input": llm_text[:500],  # Piper may have length limits
        "response_format": "wav",
    }).encode()

    tts_status, _, tts_body = http_request(
        f"{PIPER_TTS_URL}/v1/audio/speech",
        method="POST",
        data=tts_payload,
        headers={"Content-Type": "application/json"},
    )
    if tts_status != 200:
        r.error = f"TTS failed: status={tts_status}"
        return

    is_wav = tts_body[:4] == b"RIFF" and b"WAVE" in tts_body[:12]
    details.append(f"TTS output: {len(tts_body)} bytes, is_wav={is_wav}")

    r.detail = "\n".join(details)
    r.passed = is_wav


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print_banner("Dunkin Chat Voice Assistant — Integration Tests")
    print(f"  Whisper STT : {WHISPER_STT_URL}")
    print(f"  Phi-4 LLM   : {FOUNDRY_LLM_URL}")
    print(f"  Piper TTS   : {PIPER_TTS_URL}")
    print(f"  API Key set  : {'yes' if FOUNDRY_API_KEY else 'NO'}")
    if not FOUNDRY_API_KEY:
        print("  \033[33m⚠  FOUNDRY_API_KEY not set — LLM and pipeline tests will be skipped\033[0m")

    all_results: list[TestResult] = []

    # -- Health checks -------------------------------------------------------
    print_banner("1. Health Checks")
    for test_fn in [test_whisper_health, test_piper_health]:
        res = run_test(test_fn)
        all_results.append(res)
        print_result(res)

    # -- Individual service tests --------------------------------------------
    print_banner("2. Service Tests")
    for test_fn in [test_whisper_transcribe, test_llm_chat, test_piper_synthesize]:
        res = run_test(test_fn)
        all_results.append(res)
        print_result(res)

    # -- Full pipeline -------------------------------------------------------
    print_banner("3. Full Pipeline (STT → LLM → TTS)")
    res = run_test(test_full_pipeline)
    all_results.append(res)
    print_result(res)

    # -- Summary -------------------------------------------------------------
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    skipped = sum(1 for r in all_results if "skipping" in r.error.lower())
    failed = total - passed - skipped
    total_time = sum(r.duration for r in all_results)

    print_banner("Summary")
    print(f"  Total : {total}")
    print(f"  Passed: \033[32m{passed}\033[0m")
    if skipped:
        print(f"  Skipped: \033[33m{skipped}\033[0m")
    if failed:
        print(f"  Failed: \033[31m{failed}\033[0m")
    print(f"  Time  : {total_time:.2f}s")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

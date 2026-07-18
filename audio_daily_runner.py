#!/usr/bin/env python3
"""
Daily runner: scans BASE_DIR/<client>/ATENDIMENTO/ for new audio files,
transcribes them locally with Whisper, generates a structured report via
OpenRouter, and POSTs the run summary to the N8N webhook.

Idempotent: skips audio that already has a fresh transcript/report.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Setup project root
script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))
os.chdir(script_dir)

import subprocess
import tempfile

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from src.config.settings import (
    BASE_DIR,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    WHISPER_MODEL,
)
from src.utils.audio_transcriber import (
    find_audio_files,
    needs_transcription,
    transcribe_and_save,
    transcript_path_for,
)
from src.utils.audio_summarizer import (
    needs_report,
    report_path_for,
    summarize_and_save,
)

N8N_WEBHOOK_URL = os.getenv(
    "WEBHOOK_URL",
    "https://n8n.srv921079.hstgr.cloud/webhook/b657fab8-c7ff-4a0c-90cc-0b49ce9a7411",
)

LOG_FILE = script_dir / "audio_daily_runner.log"
logging.basicConfig(
    filename=str(LOG_FILE),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
# Also log to stdout when running interactively
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))
logger = logging.getLogger(__name__)


def client_folder_for(audio_path: Path) -> str:
    """Walk up from audio file to the client folder (BASE_DIR/<client>/ATENDIMENTO/...)."""
    rel = audio_path.relative_to(BASE_DIR)
    return rel.parts[0] if rel.parts else "(unknown)"


def run() -> dict:
    results = {
        "timestamp": datetime.now().isoformat(),
        "base_dir": str(BASE_DIR),
        "whisper_model": WHISPER_MODEL,
        "openrouter_model": OPENROUTER_MODEL if OPENROUTER_API_KEY else "(no API key)",
        "transcribed": [],
        "reported": [],
        "skipped": [],
        "failures": [],
    }

    audio_files = list(find_audio_files(BASE_DIR))
    logger.info(f"Found {len(audio_files)} audio file(s) under ATENDIMENTO/ folders")

    for audio in audio_files:
        client = client_folder_for(audio)
        rel_audio = audio.relative_to(BASE_DIR)

        # Stage 1 — transcription
        if needs_transcription(audio):
            try:
                logger.info(f"Transcribing: {rel_audio}")
                transcribe_and_save(audio)
                results["transcribed"].append(str(rel_audio))
            except Exception as e:
                logger.exception(f"Transcription failed for {rel_audio}")
                results["failures"].append({
                    "audio": str(rel_audio),
                    "stage": "transcribe",
                    "error": str(e),
                })
                continue
        else:
            results["skipped"].append(str(rel_audio))

        # Stage 2 — summarization (skip if no API key)
        if not OPENROUTER_API_KEY:
            continue

        transcript = transcript_path_for(audio)
        if needs_report(transcript):
            try:
                logger.info(f"Summarizing: {rel_audio}")
                summarize_and_save(transcript, client)
                results["reported"].append(str(rel_audio))
            except Exception as e:
                logger.exception(f"Summarization failed for {rel_audio}")
                results["failures"].append({
                    "audio": str(rel_audio),
                    "stage": "summarize",
                    "error": str(e),
                })

    return results


def post_to_webhook(data: dict) -> bool:
    """POST JSON results to N8N webhook via curl (matches existing cron_runner pattern)."""
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f, ensure_ascii=False)
            tmp_path = f.name

        result = subprocess.run(
            [
                "curl", "-s", "-w", "%{http_code}",
                "-X", "POST",
                "-H", "Content-Type: application/json",
                "-d", f"@{tmp_path}",
                "--max-time", "30",
                N8N_WEBHOOK_URL,
            ],
            capture_output=True,
            text=True,
            timeout=35,
        )
        os.unlink(tmp_path)

        output = result.stdout
        status_code = output[-3:] if len(output) >= 3 else "000"
        body = output[:-3]

        if result.returncode == 0 and status_code.startswith("2"):
            logger.info(f"Webhook POST success: HTTP {status_code}")
            return True
        logger.error(
            f"Webhook POST failed: HTTP {status_code}, "
            f"curl exit {result.returncode}, body: {body}, stderr: {result.stderr}"
        )
        return False
    except Exception as e:
        logger.error(f"Webhook POST failed: {e}")
        return False


def main():
    logger.info("=== Audio daily runner started ===")
    results = run()

    summary = {
        "transcribed": len(results["transcribed"]),
        "reported": len(results["reported"]),
        "skipped": len(results["skipped"]),
        "failures": len(results["failures"]),
    }
    logger.info(f"Summary: {summary}")

    results_file = script_dir / "audio_latest_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    logger.info(f"Results saved to {results_file}")

    if post_to_webhook(results):
        logger.info("Results posted to N8N successfully.")
    else:
        logger.warning("Failed to post results to N8N (continuing).")

    logger.info("=== Audio daily runner finished ===")


if __name__ == "__main__":
    main()

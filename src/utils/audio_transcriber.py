"""
Audio transcription via faster-whisper (100% local — no audio leaves the machine).

Walks BASE_DIR/<client>/ATENDIMENTO/ for audio files, transcribes new ones,
writes a sidecar `<audio>.transcricao.txt`. Idempotent: skips audio whose
transcript already exists and is newer than the audio.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

from src.config.settings import (
    ATENDIMENTO_DIR_NAME,
    AUDIO_EXTENSIONS,
    EXCLUDED_DIRS,
    TRANSCRIPT_SUFFIX,
    WHISPER_COMPUTE_TYPE,
    WHISPER_DEVICE,
    WHISPER_LANGUAGE,
    WHISPER_MODEL,
)

logger = logging.getLogger(__name__)

_model = None


def _get_model():
    """Lazy-load the Whisper model — first call downloads weights."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        logger.info(
            f"Loading Whisper model '{WHISPER_MODEL}' "
            f"(device={WHISPER_DEVICE}, compute_type={WHISPER_COMPUTE_TYPE})"
        )
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
        )
    return _model


def transcript_path_for(audio_path: Path) -> Path:
    return audio_path.parent / (audio_path.name + TRANSCRIPT_SUFFIX)


def find_audio_files(base_dir: Path) -> Iterator[Path]:
    """Yield audio files under BASE_DIR/<client>/ATENDIMENTO/ (recursive)."""
    if not base_dir.is_dir():
        logger.error(f"BASE_DIR does not exist: {base_dir}")
        return

    for client_dir in base_dir.iterdir():
        if not client_dir.is_dir():
            continue
        if client_dir.name in EXCLUDED_DIRS:
            continue
        atendimento = client_dir / ATENDIMENTO_DIR_NAME
        if not atendimento.is_dir():
            continue
        for path in atendimento.rglob('*'):
            if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
                yield path


def needs_transcription(audio_path: Path) -> bool:
    """True if the transcript is missing or older than the audio."""
    transcript = transcript_path_for(audio_path)
    if not transcript.exists():
        return True
    return audio_path.stat().st_mtime > transcript.stat().st_mtime


def transcribe(audio_path: Path) -> str:
    """Transcribe a single audio file. Returns the full text."""
    model = _get_model()
    segments, info = model.transcribe(
        str(audio_path),
        language=WHISPER_LANGUAGE,
        beam_size=5,
        vad_filter=True,
    )
    parts = [seg.text.strip() for seg in segments]
    text = ' '.join(parts).strip()
    logger.info(
        f"Transcribed {audio_path.name}: "
        f"duration={info.duration:.1f}s, language={info.language}, "
        f"chars={len(text)}"
    )
    return text


def transcribe_and_save(audio_path: Path) -> Path:
    """Transcribe audio and write the sidecar .transcricao.txt. Returns the transcript path."""
    text = transcribe(audio_path)
    transcript = transcript_path_for(audio_path)
    transcript.write_text(text, encoding='utf-8')
    logger.info(f"Saved transcript: {transcript}")
    return transcript

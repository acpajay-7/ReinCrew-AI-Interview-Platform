"""Speech-to-text with Faster-Whisper (lazy loaded). Model files download once on first use."""
import tempfile
from functools import lru_cache

from . import config


class TranscriptionError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _model():
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise TranscriptionError("faster-whisper is not installed. Run: pip install faster-whisper") from e
    return WhisperModel(config.ASR_MODEL, device="cpu", compute_type="int8")


def transcribe_bytes(audio: bytes, suffix: str = ".wav") -> str:
    if not audio:
        raise TranscriptionError("No audio received.")
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as f:  # temp file deleted automatically: recordings are not kept
        f.write(audio)
        f.flush()
        try:
            segments, _ = _model().transcribe(f.name, beam_size=1, vad_filter=True)
            return " ".join(s.text.strip() for s in segments).strip()
        except TranscriptionError:
            raise
        except Exception as e:
            raise TranscriptionError(f"Transcription failed: {e}") from e


def warm_up():
    """Load (and, on first run, download) the model before the interview so question 1 is not delayed."""
    _model()

"""Расшифровка аудио в текст с таймкодами.

Движки:
- ``faster-whisper`` (по умолчанию) — полностью локально и бесплатно;
  модель скачивается один раз с HuggingFace при первом запуске;
- ``openai`` — облачный Whisper API (нужен OPENAI_API_KEY, лимит файла 25 МБ).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .config import ConfigError, ScribeConfig
from .models import Segment, Transcript


class TranscribeEngine(Protocol):
    def transcribe(self, audio_path: Path) -> Transcript: ...


class FasterWhisperEngine:
    def __init__(
        self,
        model: str = "small",
        language: str = "",
        device: str = "auto",
        compute_type: str = "default",
        beam_size: int = 5,
        vad_filter: bool = True,
    ):
        self.model_name = model
        self.language = language or None
        self.device = device
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self._model = None

    def _load(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise ConfigError(
                "Не установлен faster-whisper. Выполните: "
                "pip install -r meeting_scribe/requirements.txt"
            ) from exc
        try:
            self._model = WhisperModel(
                self.model_name, device=self.device, compute_type=self.compute_type
            )
        except Exception:
            # Частый кейс: device=auto выбрал CUDA, а cuDNN/cuBLAS не стоят.
            # Падаем обратно на CPU — медленно, но работает везде.
            self._model = WhisperModel(
                self.model_name, device="cpu", compute_type="int8"
            )
        return self._model

    def transcribe(self, audio_path: Path) -> Transcript:
        model = self._load()
        segments_iter, info = model.transcribe(
            str(audio_path),
            language=self.language,
            beam_size=self.beam_size,
            vad_filter=self.vad_filter,
        )
        segments = [
            Segment(start=float(s.start), end=float(s.end), text=s.text.strip())
            for s in segments_iter
            if s.text.strip()
        ]
        return Transcript(
            segments=segments,
            language=getattr(info, "language", None),
            duration=getattr(info, "duration", None),
        )


class OpenAIEngine:
    """Облачный вариант. Аудио уходит в OpenAI — учитывайте конфиденциальность."""

    MAX_BYTES = 25 * 1024 * 1024

    def __init__(self, api_key: str, model: str = "whisper-1", language: str = ""):
        if not api_key:
            raise ConfigError(
                "Для engine=openai нужна переменная окружения OPENAI_API_KEY"
            )
        self.api_key = api_key
        self.model_name = model or "whisper-1"
        self.language = language or None

    def transcribe(self, audio_path: Path) -> Transcript:
        import requests  # уже есть в requirements проекта

        if audio_path.stat().st_size > self.MAX_BYTES:
            raise ConfigError(
                "Файл больше 25 МБ — лимит Whisper API. Используйте локальный "
                "engine=faster-whisper для длинных созвонов."
            )
        data = {"model": self.model_name, "response_format": "verbose_json"}
        if self.language:
            data["language"] = self.language
        with audio_path.open("rb") as fh:
            resp = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files={"file": (audio_path.name, fh)},
                data=data,
                timeout=1800,
            )
        if resp.status_code >= 400:
            raise ConfigError(f"OpenAI API {resp.status_code}: {resp.text[:300]}")
        payload = resp.json()
        segments = [
            Segment(
                start=float(s["start"]), end=float(s["end"]), text=s["text"].strip()
            )
            for s in payload.get("segments", [])
            if s.get("text", "").strip()
        ]
        return Transcript(
            segments=segments,
            language=payload.get("language"),
            duration=payload.get("duration"),
        )


def get_engine(cfg: ScribeConfig) -> TranscribeEngine:
    t = cfg.transcribe
    if t.engine == "faster-whisper":
        return FasterWhisperEngine(
            model=t.model,
            language=t.language,
            device=t.device,
            compute_type=t.compute_type,
            beam_size=t.beam_size,
            vad_filter=t.vad_filter,
        )
    if t.engine == "openai":
        return OpenAIEngine(cfg.openai_api_key, model=t.model, language=t.language)
    raise ConfigError(
        f"Неизвестный engine={t.engine!r}. Допустимо: faster-whisper | openai"
    )

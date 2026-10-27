"""Склейка всего процесса: аудио -> стенограмма -> файлы -> Notion/Docs.

Структура результата на диске:
    recordings/
      2026-10-27_1430_Планёрка/
        audio.wav          (если record.keep_audio)
        transcript.md / .txt / .srt / .json
"""

from __future__ import annotations

import re
import shutil
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .config import ConfigError, ScribeConfig
from .formatting import to_json, to_markdown, to_srt, to_text
from .models import Transcript
from .publishers import build_publishers
from .recorder import Recorder
from .transcribe import TranscribeEngine, get_engine


@dataclass
class PipelineResult:
    title: str
    session_dir: Path
    audio_path: Path
    transcript: Transcript
    files: dict[str, Path] = field(default_factory=dict)
    published: dict[str, str] = field(default_factory=dict)  # имя -> URL
    publish_errors: dict[str, str] = field(default_factory=dict)  # имя -> ошибка


def slugify(title: str, limit: int = 60) -> str:
    slug = re.sub(r"[^\w\- ]+", "", title, flags=re.UNICODE).strip()
    slug = re.sub(r"[\s_]+", "_", slug)
    return (slug or "meeting")[:limit]


def default_title(when: datetime | None = None) -> str:
    when = when or datetime.now()
    return f"Созвон {when:%Y-%m-%d %H:%M}"


def make_session_dir(out_root: Path, title: str, when: datetime) -> Path:
    session = out_root / f"{when:%Y-%m-%d_%H%M}_{slugify(title)}"
    session.mkdir(parents=True, exist_ok=True)
    return session


def process_audio(
    audio_path: Path,
    cfg: ScribeConfig,
    title: str | None = None,
    engine: TranscribeEngine | None = None,
    publishers: dict | None = None,
    out_root: Path | None = None,
    session_dir: Path | None = None,
    when: datetime | None = None,
) -> PipelineResult:
    """Расшифровывает готовый аудиофайл, пишет файлы и публикует.

    Ошибка публикации НЕ роняет процесс: локальные файлы уже сохранены,
    ошибка вернётся в ``result.publish_errors``.
    """
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise ConfigError(f"Аудиофайл не найден: {audio_path}")
    when = when or datetime.now()
    title = title or default_title(when)
    out_root = out_root or Path(cfg.record.output_dir)
    session_dir = session_dir or make_session_dir(out_root, title, when)

    # Аудио кладём рядом со стенограммой (если оно ещё не там и так настроено).
    stored_audio = audio_path
    if cfg.record.keep_audio and audio_path.parent.resolve() != session_dir.resolve():
        stored_audio = session_dir / f"audio{audio_path.suffix or '.wav'}"
        shutil.copy2(audio_path, stored_audio)

    engine = engine or get_engine(cfg)
    transcript = engine.transcribe(audio_path)

    meta = {
        "date": f"{when:%Y-%m-%d %H:%M}",
        "audio_file": stored_audio.name if cfg.record.keep_audio else audio_path.name,
    }
    files = {
        "md": session_dir / "transcript.md",
        "txt": session_dir / "transcript.txt",
        "srt": session_dir / "transcript.srt",
        "json": session_dir / "transcript.json",
    }
    files["md"].write_text(to_markdown(transcript, title, meta), encoding="utf-8")
    files["txt"].write_text(to_text(transcript), encoding="utf-8")
    files["srt"].write_text(to_srt(transcript), encoding="utf-8")
    files["json"].write_text(to_json(transcript), encoding="utf-8")

    result = PipelineResult(
        title=title,
        session_dir=session_dir,
        audio_path=stored_audio,
        transcript=transcript,
        files=files,
    )
    if publishers is None:
        publishers = build_publishers(cfg)
    for name, publisher in publishers.items():
        try:
            result.published[name] = publisher.publish(title, transcript, meta)
        except Exception as exc:  # публикация — дополнение, файлы уже на диске
            result.publish_errors[name] = str(exc)
    return result


def record_session(
    cfg: ScribeConfig,
    title: str | None = None,
    max_seconds: float | None = None,
    stop_event: threading.Event | None = None,
    engine: TranscribeEngine | None = None,
    publishers: dict | None = None,
    out_root: Path | None = None,
) -> PipelineResult:
    """Пишет звук до Ctrl+C / stop_event / истечения max_seconds, затем обрабатывает."""
    when = datetime.now()
    title = title or default_title(when)
    out_root = out_root or Path(cfg.record.output_dir)
    session_dir = make_session_dir(out_root, title, when)
    audio_path = session_dir / "audio.wav"

    recorder = Recorder(cfg.record)
    recorder.start(audio_path, max_seconds=max_seconds)
    try:
        while recorder.is_running:
            if stop_event is not None and stop_event.is_set():
                break
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass  # штатное завершение вручную
    finally:
        recorder.stop()

    if not audio_path.is_file() or audio_path.stat().st_size < 1024:
        raise ConfigError(
            f"Запись пуста или отсутствует: {audio_path}. "
            "Проверьте устройства (`python -m meeting_scribe devices`)."
        )
    return process_audio(
        audio_path,
        cfg,
        title=title,
        engine=engine,
        publishers=publishers,
        session_dir=session_dir,
        when=when,
    )

"""Конфигурация агента.

Формат — TOML (читается стандартным ``tomllib``, лишних зависимостей нет).
Секреты (токены) берутся из переменных окружения и в файл не пишутся:
``NOTION_TOKEN``, ``OPENAI_API_KEY``.

Поиск конфига (первый найденный):
1. путь из ``--config`` / переменной ``SCRIBE_CONFIG``;
2. ``./scribe.toml`` в текущей папке;
3. ``~/.config/meeting_scribe/config.toml``.
Если файл не найден — используются значения по умолчанию.
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


class ConfigError(RuntimeError):
    pass


@dataclass
class RecordConfig:
    # Имена/индексы аудиоустройств. Узнать: python -m meeting_scribe devices
    mic_device: str = ""  # микрофон
    system_device: str = ""  # системный звук (собеседники)
    output_dir: str = "recordings"
    keep_audio: bool = True  # оставлять .wav рядом со стенограммой


@dataclass
class TranscribeConfig:
    engine: str = "faster-whisper"  # faster-whisper | openai
    model: str = "small"  # tiny/base/small/medium/large-v3 (для openai: whisper-1)
    language: str = ""  # "" = автоопределение, или ru/en/...
    device: str = "auto"  # auto | cpu | cuda
    compute_type: str = "default"
    beam_size: int = 5
    vad_filter: bool = True  # вырезать тишину (быстрее и чище)


@dataclass
class NotionConfig:
    parent_page_id: str = ""  # создать страницу внутри этой страницы
    database_id: str = ""  # ...или запись в этой базе данных
    title_property: str = "Name"  # имя title-колонки базы


@dataclass
class GoogleDocsConfig:
    credentials_json: str = ""  # путь к JSON сервисного аккаунта Google
    folder_id: str = ""  # папка на Drive (необязательно)
    share_with_email: str = ""  # кому расшарить документ (вам)


@dataclass
class CalendarConfig:
    ics_source: str = ""  # URL (.ics) или путь к файлу календаря
    poll_seconds: int = 60
    grace_seconds: int = 120  # писать ещё N сек после конца события
    record_all: bool = False  # писать все события, а не только созвоны
    keywords: list[str] = field(
        default_factory=lambda: [
            "meet.google",
            "zoom.",
            "teams.microsoft",
            "telemost",
            "webex",
            "созвон",
            "видеовстреч",
        ]
    )


@dataclass
class ScribeConfig:
    record: RecordConfig = field(default_factory=RecordConfig)
    transcribe: TranscribeConfig = field(default_factory=TranscribeConfig)
    notion: NotionConfig = field(default_factory=NotionConfig)
    google_docs: GoogleDocsConfig = field(default_factory=GoogleDocsConfig)
    calendar: CalendarConfig = field(default_factory=CalendarConfig)
    publish: list[str] = field(default_factory=list)  # ["notion", "google_docs"]
    source_path: Path | None = None

    # --- секреты только из окружения ---
    @property
    def notion_token(self) -> str:
        return os.environ.get("NOTION_TOKEN", "")

    @property
    def openai_api_key(self) -> str:
        return os.environ.get("OPENAI_API_KEY", "")


def _fill(obj, data: dict) -> None:
    for key, value in (data or {}).items():
        if hasattr(obj, key):
            setattr(obj, key, value)


def find_config_path(explicit: str | None = None) -> Path | None:
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("SCRIBE_CONFIG"):
        candidates.append(Path(os.environ["SCRIBE_CONFIG"]))
    candidates += [
        Path.cwd() / "scribe.toml",
        Path.home() / ".config" / "meeting_scribe" / "config.toml",
    ]
    for path in candidates:
        if path.is_file():
            return path
    if explicit:
        raise ConfigError(f"Файл конфига не найден: {explicit}")
    return None


def load_config(explicit_path: str | None = None) -> ScribeConfig:
    cfg = ScribeConfig()
    path = find_config_path(explicit_path)
    if path is None:
        return cfg
    try:
        with path.open("rb") as fh:
            raw = tomllib.load(fh)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Ошибка в {path}: {exc}") from exc

    cfg.source_path = path
    _fill(cfg.record, raw.get("record", {}))
    _fill(cfg.transcribe, raw.get("transcribe", {}))
    _fill(cfg.notion, raw.get("notion", {}))
    _fill(cfg.google_docs, raw.get("google_docs", {}))
    _fill(cfg.calendar, raw.get("calendar", {}))
    cfg.publish = list(raw.get("publish", []))
    return cfg

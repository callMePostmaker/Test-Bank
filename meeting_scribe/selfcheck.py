"""Самопроверка окружения: что установлено, чего не хватает.

Запуск: python -m meeting_scribe check
Честно различает: ok / warn (опционально и не настроено) / fail.
"""

from __future__ import annotations

import shutil
import sys
import wave
from dataclasses import dataclass
from pathlib import Path

from .config import ScribeConfig
from .models import Segment, Transcript


@dataclass
class CheckResult:
    name: str
    status: str  # ok | warn | fail
    detail: str = ""


def _write_silent_wav(path: Path) -> None:
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * 1600)  # 0.1 c тишины


def _check_pipeline(cfg: ScribeConfig, workdir: Path) -> CheckResult:
    """Прогоняет пайплайн end-to-end с фейковым движком (без модели и сети)."""
    from .pipeline import process_audio

    class FakeEngine:
        def transcribe(self, audio_path: Path) -> Transcript:
            return Transcript(
                segments=[Segment(0.0, 1.0, "проверка пайплайна")],
                language="ru",
                duration=1.0,
            )

    try:
        wav = workdir / "selfcheck.wav"
        _write_silent_wav(wav)
        result = process_audio(
            wav, cfg, title="selfcheck", engine=FakeEngine(),
            publishers={}, out_root=workdir / "out",
        )
        ok = result.files["md"].is_file() and "проверка пайплайна" in result.files["md"].read_text(encoding="utf-8")
        return CheckResult("пайплайн end-to-end (без модели)", "ok" if ok else "fail", "файлы стенограммы создаются")
    except Exception as exc:
        return CheckResult("пайплайн end-to-end (без модели)", "fail", repr(exc))


def run_checks(cfg: ScribeConfig, workdir: Path) -> list[CheckResult]:
    workdir = Path(workdir)
    workdir.mkdir(parents=True, exist_ok=True)
    checks: list[CheckResult] = []

    checks.append(CheckResult(
        "python >= 3.11",
        "ok" if sys.version_info >= (3, 11) else "fail",
        sys.version.split()[0],
    ))
    ffmpeg = shutil.which("ffmpeg")
    checks.append(CheckResult(
        "ffmpeg", "ok" if ffmpeg else "fail",
        ffmpeg or "не найден — см. README (winget/brew/apt install ffmpeg)",
    ))
    checks.append(CheckResult(
        "конфиг scribe.toml", "ok" if cfg.source_path else "warn",
        str(cfg.source_path) if cfg.source_path else "не найден — используются значения по умолчанию",
    ))
    devices_set = bool(cfg.record.mic_device or cfg.record.system_device)
    checks.append(CheckResult(
        "аудиоустройства заданы", "ok" if devices_set else "warn",
        f"mic={cfg.record.mic_device!r} system={cfg.record.system_device!r}"
        if devices_set else "пусто — выполните `python -m meeting_scribe devices`",
    ))

    if cfg.transcribe.engine == "openai":
        checks.append(CheckResult(
            "OPENAI_API_KEY", "ok" if cfg.openai_api_key else "fail",
            "задан" if cfg.openai_api_key else "не задан, а engine=openai",
        ))
    else:
        try:
            from faster_whisper import WhisperModel

            checks.append(CheckResult("faster-whisper установлен", "ok"))
            try:
                WhisperModel(cfg.transcribe.model, device="cpu", compute_type="int8")
                checks.append(CheckResult(f"модель '{cfg.transcribe.model}' загружается", "ok", "кеш готов"))
            except Exception as exc:
                checks.append(CheckResult(
                    f"модель '{cfg.transcribe.model}' загружается", "fail",
                    f"{exc} (при первом запуске нужен доступ к huggingface.co)",
                ))
        except ImportError:
            checks.append(CheckResult(
                "faster-whisper установлен", "fail",
                "pip install -r meeting_scribe/requirements.txt",
            ))

    if "notion" in cfg.publish:
        ok = bool(cfg.notion_token and (cfg.notion.parent_page_id or cfg.notion.database_id))
        checks.append(CheckResult(
            "Notion настроен", "ok" if ok else "fail",
            "токен и страница/база заданы" if ok else "нужны NOTION_TOKEN и parent_page_id/database_id",
        ))
    else:
        checks.append(CheckResult("Notion настроен", "warn", "не включён в publish (опционально)"))

    if cfg.calendar.ics_source:
        checks.append(CheckResult("календарь (watch)", "ok", cfg.calendar.ics_source[:60]))
    else:
        checks.append(CheckResult("календарь (watch)", "warn", "ics_source пуст — режим watch недоступен (опционально)"))

    checks.append(_check_pipeline(cfg, workdir))
    return checks

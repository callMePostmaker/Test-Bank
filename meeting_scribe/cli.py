"""Командная строка агента-стенографиста.

  python -m meeting_scribe check                 самопроверка окружения
  python -m meeting_scribe devices               список аудиоустройств
  python -m meeting_scribe record                запись до Ctrl+C -> стенограмма
  python -m meeting_scribe record --name "Планёрка" --duration 3600
  python -m meeting_scribe transcribe call.wav   расшифровать готовый файл
  python -m meeting_scribe watch                 автозапись по календарю (.ics)
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path

from .config import ConfigError, ScribeConfig, load_config
from .selfcheck import run_checks

CONSENT_WARNING = (
    "⚠️  Идёт запись созвона. Убедитесь, что участники уведомлены о записи "
    "и согласны с ней."
)


def _print_result(result) -> None:
    print(f"\n✅ Готово: «{result.title}»")
    print(f"   Папка:      {result.session_dir}")
    print(f"   Стенограмма: {result.files.get('md')}")
    print(f"   Сегментов:  {len(result.transcript)}")
    for name, url in result.published.items():
        print(f"   {name}: {url}")
    for name, err in result.publish_errors.items():
        print(f"   ⚠️ Публикация в {name} не удалась: {err} (файлы сохранены локально)")


def cmd_check(cfg: ScribeConfig) -> int:
    icons = {"ok": "✅", "warn": "⚠️", "fail": "❌"}
    with tempfile.TemporaryDirectory(prefix="scribe-check-") as tmp:
        results = run_checks(cfg, Path(tmp))
    failed = 0
    for r in results:
        print(f"{icons.get(r.status, '?')} {r.name}: {r.detail}")
        failed += r.status == "fail"
    print("\nИтог:", "окружение готово" if not failed else f"не готово, проблем: {failed} (см. ❌ выше, ⚠️ опционально)")
    return 1 if failed else 0


def cmd_devices(cfg: ScribeConfig) -> int:
    from .recorder import list_devices_command

    cmd, hint = list_devices_command()
    if not shutil.which(cmd[0]):
        print(f"Команда `{cmd[0]}` не найдена. Установите её (см. README) и повторите.")
        return 1
    # ffmpeg при -list_devices пишет список в stderr и выходит с ошибкой — это нормально.
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print((proc.stdout or "") + (proc.stderr or ""))
    print("Подсказка:", hint)
    print('Укажите устройства в scribe.toml, секция [record]: mic_device / system_device')
    return 0


def cmd_record(cfg: ScribeConfig, args) -> int:
    from .pipeline import record_session

    print(CONSENT_WARNING)
    print("🎙️ Запись началась. Ctrl+C — остановить и расшифровать.")
    result = record_session(
        cfg,
        title=args.name,
        max_seconds=args.duration,
        publishers={} if args.no_publish else None,
    )
    _print_result(result)
    return 0


def cmd_transcribe(cfg: ScribeConfig, args) -> int:
    from .pipeline import process_audio

    result = process_audio(
        Path(args.file),
        cfg,
        title=args.name,
        publishers={} if args.no_publish else None,
    )
    _print_result(result)
    return 0


def cmd_watch(cfg: ScribeConfig, args) -> int:
    from .calendar_watch import CalEvent, CalendarWatcher
    from .pipeline import record_session

    if not cfg.calendar.ics_source:
        raise ConfigError(
            "Режим watch: укажите calendar.ics_source в scribe.toml "
            "(URL .ics-фида календаря или путь к файлу — см. README)"
        )

    def on_call_start(event: CalEvent) -> None:
        now = datetime.now().astimezone()
        seconds_left = (event.end - now).total_seconds() + cfg.calendar.grace_seconds
        print(f"\n🎙️ [{now:%H:%M}] Созвон начался: «{event.summary}» — пишу до {event.end:%H:%M}", flush=True)
        print(CONSENT_WARNING, flush=True)
        try:
            result = record_session(
                cfg, title=event.summary, max_seconds=max(seconds_left, 60)
            )
            _print_result(result)
        except Exception as exc:
            print(f"❌ Ошибка записи созвона «{event.summary}»: {exc}", flush=True)

    watcher = CalendarWatcher(cfg.calendar, on_call_start)
    print(f"👁️ Слежу за календарём (опрос каждые {cfg.calendar.poll_seconds} c). Ctrl+C — выход.")
    stop = threading.Event()
    try:
        watcher.run(stop)
    except KeyboardInterrupt:
        print("\nОстановлено.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", help="путь к scribe.toml (по умолчанию ищется автоматически)")

    parser = argparse.ArgumentParser(
        prog="meeting_scribe",
        description="Локальный агент-стенографист созвонов (запись -> расшифровка -> Notion/Google Docs)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("check", parents=[common], help="самопроверка окружения")
    sub.add_parser("devices", parents=[common], help="список аудиоустройств для конфига")

    p_record = sub.add_parser("record", parents=[common], help="писать созвон до Ctrl+C")
    p_record.add_argument("--name", help="название созвона")
    p_record.add_argument("--duration", type=int, help="макс. длительность записи, сек")
    p_record.add_argument("--no-publish", action="store_true", help="только локальные файлы, без Notion/Docs")

    p_tr = sub.add_parser("transcribe", parents=[common], help="расшифровать готовый аудиофайл")
    p_tr.add_argument("file", help="путь к аудио (wav/mp3/m4a...)")
    p_tr.add_argument("--name", help="название созвона")
    p_tr.add_argument("--no-publish", action="store_true")

    sub.add_parser("watch", parents=[common], help="автозапись созвонов по календарю (.ics)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.config)
        if args.command == "check":
            return cmd_check(cfg)
        if args.command == "devices":
            return cmd_devices(cfg)
        if args.command == "record":
            return cmd_record(cfg, args)
        if args.command == "transcribe":
            return cmd_transcribe(cfg, args)
        if args.command == "watch":
            return cmd_watch(cfg, args)
    except ConfigError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

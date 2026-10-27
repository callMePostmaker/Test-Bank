"""Автозапись по календарю: ICS-фид -> событие началось -> запись пошла.

Работает с любым календарём, умеющим отдавать .ics:
Google Calendar (секретная iCal-ссылка), Outlook (опубликованный календарь),
Яндекс Календарь (экспорт), Nextcloud и т.д.

Повторяющиеся события: поддерживаются RRULE FREQ=DAILY и FREQ=WEEKLY
(в т.ч. BYDAY, INTERVAL, COUNT, UNTIL) — этого хватает на дейлики и планёрки.
MONTHLY/YEARLY и EXDATE не разворачиваются (запишется первое вхождение).
"""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from .config import CalendarConfig

BYDAY = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}


@dataclass
class CalEvent:
    uid: str
    summary: str
    start: datetime  # aware, локальная TZ
    end: datetime
    location: str = ""
    description: str = ""

    @property
    def key(self) -> str:
        return f"{self.uid}|{self.start.isoformat()}"


def _unfold(text: str) -> list[str]:
    """ICS сворачивает длинные строки: продолжение начинается с пробела/таба."""
    lines: list[str] = []
    for raw in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if raw[:1] in (" ", "\t") and lines:
            lines[-1] += raw[1:]
        elif raw.strip():
            lines.append(raw)
    return lines


def _unescape(value: str) -> str:
    return (
        value.replace("\\n", "\n")
        .replace("\\,", ",")
        .replace("\\;", ";")
        .replace("\\\\", "\\")
        .strip()
    )


def _parse_dt(value: str, params: dict) -> datetime | None:
    """Парсит DTSTART/DTEND. События на весь день (VALUE=DATE) -> None."""
    value = value.strip()
    if params.get("VALUE") == "DATE" or len(value) == 8:
        return None
    is_utc = value.endswith("Z")
    raw = value.rstrip("Z")
    try:
        dt = datetime.strptime(raw, "%Y%m%dT%H%M%S")
    except ValueError:
        return None
    tzid = params.get("TZID")
    if is_utc:
        dt = dt.replace(tzinfo=timezone.utc)
    elif tzid:
        try:
            dt = dt.replace(tzinfo=ZoneInfo(tzid))
        except Exception:
            dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    else:  # «плавающее» время — считаем локальным
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt.astimezone()  # приводим к локальной TZ


def _raw_events(text: str) -> list[dict]:
    events, current = [], None
    for line in _unfold(text):
        if line == "BEGIN:VEVENT":
            current = {}
        elif line == "END:VEVENT" and current is not None:
            events.append(current)
            current = None
        elif current is not None and ":" in line:
            left, _, value = line.partition(":")
            parts = left.split(";")
            name = parts[0].upper()
            params = {}
            for p in parts[1:]:
                if "=" in p:
                    k, _, v = p.partition("=")
                    params[k.upper()] = v.strip('"')
            current.setdefault(name, []).append((params, value))
    return events


def _first(raw: dict, name: str) -> tuple[dict, str]:
    values = raw.get(name) or [({}, "")]
    return values[0]


def _expand(raw: dict, window_start: datetime, window_end: datetime) -> list[CalEvent]:
    s_params, s_value = _first(raw, "DTSTART")
    e_params, e_value = _first(raw, "DTEND")
    start = _parse_dt(s_value, s_params)
    if start is None:  # весь день или битая дата
        return []
    end = _parse_dt(e_value, e_params) if e_value else None
    duration = (end - start) if end and end > start else timedelta(hours=1)

    base = dict(
        uid=_unescape(_first(raw, "UID")[1]) or f"no-uid-{start.isoformat()}",
        summary=_unescape(_first(raw, "SUMMARY")[1]) or "Без названия",
        location=_unescape(_first(raw, "LOCATION")[1]),
        description=_unescape(_first(raw, "DESCRIPTION")[1]),
    )

    _, rrule_raw = _first(raw, "RRULE")
    if not rrule_raw:
        ev = CalEvent(start=start, end=start + duration, **base)
        return [ev] if window_start <= ev.end and ev.start <= window_end else []

    rule = {}
    for part in rrule_raw.split(";"):
        if "=" in part:
            k, _, v = part.partition("=")
            rule[k.upper()] = v
    freq = rule.get("FREQ", "")
    if freq not in ("DAILY", "WEEKLY"):
        ev = CalEvent(start=start, end=start + duration, **base)
        return [ev] if window_start <= ev.end and ev.start <= window_end else []

    interval = max(int(rule.get("INTERVAL", "1") or 1), 1)
    count_limit = int(rule["COUNT"]) if rule.get("COUNT") else None
    until = _parse_dt(rule["UNTIL"], {}) if rule.get("UNTIL") else None
    bydays = (
        {BYDAY[d.strip().upper()] for d in rule["BYDAY"].split(",") if d.strip().upper() in BYDAY}
        if rule.get("BYDAY")
        else set()
    )
    start_date = start.date()
    start_monday = start_date - timedelta(days=start_date.weekday())

    def matches(day) -> bool:
        if freq == "DAILY":
            return (day - start_date).days % interval == 0
        week_idx = (day - start_monday).days // 7
        if week_idx % interval != 0:
            return False
        return day.weekday() in bydays if bydays else day.weekday() == start_date.weekday()

    out: list[CalEvent] = []
    occurrences = 0
    day = start_date
    limit_date = max(window_end.date(), start_date)
    for _ in range(20_000):  # предохранитель от вечных правил
        if day > limit_date:
            break
        if matches(day):
            occ_start = datetime.combine(day, start.timetz())
            if until and occ_start > until:
                break
            occurrences += 1
            if count_limit and occurrences > count_limit:
                break
            if occ_start >= start:
                ev = CalEvent(start=occ_start, end=occ_start + duration, **base)
                if window_start <= ev.end and ev.start <= window_end:
                    out.append(ev)
        day += timedelta(days=1)
    return out


def parse_ics(
    text: str,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
) -> list[CalEvent]:
    now = datetime.now().astimezone()
    window_start = window_start or (now - timedelta(days=1))
    window_end = window_end or (now + timedelta(days=2))
    events: list[CalEvent] = []
    for raw in _raw_events(text):
        events.extend(_expand(raw, window_start, window_end))
    return sorted(events, key=lambda e: e.start)


def is_call_event(event: CalEvent, keywords: list[str], record_all: bool = False) -> bool:
    if record_all:
        return True
    haystack = f"{event.summary}\n{event.location}\n{event.description}".lower()
    return any(kw.lower() in haystack for kw in keywords)


def fetch_ics(source: str) -> str:
    if source.startswith(("http://", "https://")):
        import requests

        resp = requests.get(source, timeout=30)
        resp.raise_for_status()
        return resp.text
    return Path(source).read_text(encoding="utf-8")


class CalendarWatcher:
    """Опрашивает календарь и вызывает on_call_start в начале созвона.

    Обработанные события помечаются в state-файле, чтобы перезапуск агента
    не записывал один созвон дважды. Колбэк выполняется синхронно (запись
    блокирует цикл) — два созвона одновременно не пишутся.
    """

    def __init__(
        self,
        cfg: CalendarConfig,
        on_call_start: Callable[[CalEvent], None],
        state_path: Path | None = None,
    ):
        self.cfg = cfg
        self.on_call_start = on_call_start
        self.state_path = state_path or Path(".scribe_state.json")
        self._processed: set[str] = set()
        if self.state_path.is_file():
            try:
                self._processed = set(json.loads(self.state_path.read_text(encoding="utf-8")))
            except (ValueError, OSError):
                self._processed = set()

    def _mark_processed(self, event: CalEvent) -> None:
        self._processed.add(event.key)
        self.state_path.write_text(
            json.dumps(sorted(self._processed)), encoding="utf-8"
        )

    def poll_once(self, now: datetime | None = None) -> list[CalEvent]:
        now = now or datetime.now().astimezone()
        text = fetch_ics(self.cfg.ics_source)
        events = parse_ics(
            text, window_start=now - timedelta(hours=2), window_end=now + timedelta(hours=2)
        )
        triggered = []
        for ev in events:
            due = ev.start - timedelta(seconds=30) <= now <= ev.end
            if not due or ev.key in self._processed:
                continue
            if not is_call_event(ev, self.cfg.keywords, self.cfg.record_all):
                continue
            self._mark_processed(ev)
            triggered.append(ev)
            self.on_call_start(ev)
        return triggered

    def run(self, stop_event: threading.Event | None = None) -> None:
        stop_event = stop_event or threading.Event()
        while not stop_event.is_set():
            try:
                self.poll_once()
            except Exception as exc:  # сеть моргнула — не падаем, ждём следующий круг
                print(f"[watch] ошибка опроса календаря: {exc}", flush=True)
            stop_event.wait(self.cfg.poll_seconds)

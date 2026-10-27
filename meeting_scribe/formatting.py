"""Рендер стенограммы в Markdown / чистый текст / SRT / JSON."""

from __future__ import annotations

import json
from dataclasses import asdict

from .models import Transcript


def fmt_ts(seconds: float) -> str:
    """75.2 -> '01:15'; 3725 -> '1:02:05'."""
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def fmt_srt_ts(seconds: float) -> str:
    """Для субтитров: '00:01:15,200'."""
    ms_total = int(round(seconds * 1000))
    h, rem = divmod(ms_total, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def fmt_duration(seconds: float | None) -> str:
    if not seconds:
        return "—"
    return fmt_ts(seconds)


def to_markdown(transcript: Transcript, title: str, meta: dict | None = None) -> str:
    meta = meta or {}
    lines = [f"# {title}", ""]
    if meta.get("date"):
        lines.append(f"- **Дата:** {meta['date']}")
    lines.append(f"- **Длительность:** {fmt_duration(transcript.duration)}")
    if transcript.language:
        lines.append(f"- **Язык:** {transcript.language}")
    if meta.get("audio_file"):
        lines.append(f"- **Аудио:** `{meta['audio_file']}`")
    lines += ["", "## Стенограмма", ""]
    for seg in transcript.segments:
        lines.append(f"[{fmt_ts(seg.start)}] {seg.text.strip()}")
        lines.append("")
    if not transcript.segments:
        lines.append("_(речь не распознана)_")
    return "\n".join(lines).rstrip() + "\n"


def to_text(transcript: Transcript) -> str:
    body = "\n".join(
        f"[{fmt_ts(seg.start)}] {seg.text.strip()}" for seg in transcript.segments
    )
    return body + ("\n" if body else "")


def to_srt(transcript: Transcript) -> str:
    blocks = []
    for i, seg in enumerate(transcript.segments, 1):
        blocks.append(
            f"{i}\n{fmt_srt_ts(seg.start)} --> {fmt_srt_ts(seg.end)}\n{seg.text.strip()}\n"
        )
    return "\n".join(blocks)


def to_json(transcript: Transcript) -> str:
    return json.dumps(asdict(transcript), ensure_ascii=False, indent=2)

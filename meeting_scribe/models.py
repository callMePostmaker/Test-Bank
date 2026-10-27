"""Общие структуры данных: сегмент речи и стенограмма целиком."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Segment:
    """Один кусок речи с таймкодами (секунды от начала записи)."""

    start: float
    end: float
    text: str


@dataclass
class Transcript:
    segments: list[Segment] = field(default_factory=list)
    language: str | None = None
    duration: float | None = None  # длительность аудио, сек

    @property
    def full_text(self) -> str:
        return " ".join(s.text.strip() for s in self.segments if s.text.strip())

    def __len__(self) -> int:
        return len(self.segments)

"""Тесты meeting_scribe. Запуск: pytest meeting_scribe/tests -q

Сеть, ffmpeg и модель Whisper не нужны: движок и HTTP подменяются фейками.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from meeting_scribe.calendar_watch import is_call_event, parse_ics
from meeting_scribe.config import ConfigError, RecordConfig, ScribeConfig, load_config
from meeting_scribe.formatting import fmt_ts, to_markdown, to_srt
from meeting_scribe.models import Segment, Transcript
from meeting_scribe.pipeline import process_audio, slugify
from meeting_scribe.publishers import PublishError
from meeting_scribe.publishers.notion import NotionPublisher
from meeting_scribe.recorder import build_ffmpeg_command

# ---------------------------------------------------------------- formatting


def test_fmt_ts():
    assert fmt_ts(0) == "00:00"
    assert fmt_ts(75.9) == "01:15"
    assert fmt_ts(3725) == "1:02:05"


def sample_transcript() -> Transcript:
    return Transcript(
        segments=[Segment(0.0, 4.5, "Привет всем"), Segment(75.0, 80.0, "Второй вопрос")],
        language="ru",
        duration=80.0,
    )


def test_markdown_and_srt():
    md = to_markdown(sample_transcript(), "Планёрка", {"date": "2026-10-27 14:30"})
    assert md.startswith("# Планёрка")
    assert "[00:00] Привет всем" in md
    assert "[01:15] Второй вопрос" in md
    srt = to_srt(sample_transcript())
    assert "00:00:00,000 --> 00:00:04,500" in srt


# ------------------------------------------------------------------ recorder


def test_ffmpeg_command_linux_two_inputs():
    cfg = RecordConfig(mic_device="mic0", system_device="out.monitor")
    cmd = build_ffmpeg_command(cfg, Path("a.wav"), os_name="linux")
    assert cmd.count("pulse") == 2
    assert any("amix=inputs=2" in part for part in cmd)
    assert cmd[-1] == "a.wav"


def test_ffmpeg_command_windows_and_macos():
    cfg = RecordConfig(mic_device="Microphone", system_device="Stereo Mix")
    cmd = build_ffmpeg_command(cfg, Path("a.wav"), os_name="windows")
    assert "dshow" in cmd and "audio=Stereo Mix" in cmd
    cfg2 = RecordConfig(mic_device="0", system_device="2")
    cmd2 = build_ffmpeg_command(cfg2, Path("a.wav"), os_name="macos")
    assert "avfoundation" in cmd2 and ":2" in cmd2


def test_ffmpeg_single_input_no_mix():
    cmd = build_ffmpeg_command(RecordConfig(mic_device="m"), Path("a.wav"), os_name="linux")
    assert not any("amix" in p for p in cmd)


def test_ffmpeg_no_devices_raises():
    with pytest.raises(ConfigError):
        build_ffmpeg_command(RecordConfig(), Path("a.wav"), os_name="linux")


# -------------------------------------------------------------------- notion


class FakeResponse:
    def __init__(self, status=200, payload=None):
        self.status_code = status
        self._payload = payload or {}
        self.text = json.dumps(self._payload)

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def post(self, url, headers=None, json=None, timeout=None):
        self.calls.append(("POST", url, json))
        if self.fail:
            return FakeResponse(401, {"message": "unauthorized"})
        return FakeResponse(200, {"id": "page-123", "url": "https://notion.so/page-123"})

    def patch(self, url, headers=None, json=None, timeout=None):
        self.calls.append(("PATCH", url, json))
        return FakeResponse(200, {})


def test_notion_publish_batches_blocks():
    # 250 сегментов -> 253 блока -> 1 POST (100) + 2 PATCH (100 + 53)
    tr = Transcript(segments=[Segment(i * 5.0, i * 5 + 4, f"реплика {i}") for i in range(250)])
    session = FakeSession()
    pub = NotionPublisher("tok", parent_page_id="parent-1", session=session)
    url = pub.publish("Созвон", tr, {"date": "2026-10-27"})
    assert url == "https://notion.so/page-123"
    kinds = [c[0] for c in session.calls]
    assert kinds == ["POST", "PATCH", "PATCH"]
    assert len(session.calls[0][2]["children"]) == 100


def test_notion_requires_exactly_one_parent():
    with pytest.raises(PublishError):
        NotionPublisher("tok", parent_page_id="a", database_id="b", session=FakeSession())
    with pytest.raises(PublishError):
        NotionPublisher("tok", session=FakeSession())


def test_notion_api_error_raises():
    pub = NotionPublisher("bad", parent_page_id="p", session=FakeSession(fail=True))
    with pytest.raises(PublishError):
        pub.publish("t", sample_transcript())


# ----------------------------------------------------------------- календарь

ICS = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:evt-1
SUMMARY:Планёрка
DTSTART:20261027T110000Z
DTEND:20261027T113000Z
LOCATION:https://meet.google.com/abc-defg-hij
END:VEVENT
BEGIN:VEVENT
UID:daily-1
SUMMARY:Дейли созвон
DTSTART;TZID=Europe/Moscow:20261026T100000
DTEND;TZID=Europe/Moscow:20261026T101500
RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE
END:VEVENT
END:VCALENDAR
"""


def test_parse_ics_and_recurrence():
    start = datetime(2026, 10, 27, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 10, 28, 23, 59, tzinfo=timezone.utc)
    events = parse_ics(ICS, window_start=start, window_end=end)
    by_uid = {e.uid: e for e in events}
    assert "evt-1" in by_uid
    assert by_uid["evt-1"].summary == "Планёрка"
    # 2026-10-27 — вторник: WEEKLY BYDAY MO,TU,WE -> 27 и 28 числа
    dailies = [e for e in events if e.uid == "daily-1"]
    assert {e.start.day for e in dailies} == {27, 28}
    assert all(e.start.tzinfo is not None for e in events)


def test_is_call_event():
    start = datetime(2026, 10, 27, 0, 0, tzinfo=timezone.utc)
    events = parse_ics(ICS, start, start + timedelta(days=1))
    ev = next(e for e in events if e.uid == "evt-1")
    assert is_call_event(ev, ["meet.google"])
    assert not is_call_event(ev, ["zoom."])
    assert is_call_event(ev, [], record_all=True)


# ------------------------------------------------------------------ пайплайн


class FakeEngine:
    def transcribe(self, audio_path: Path) -> Transcript:
        return sample_transcript()


class FakePublisher:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def publish(self, title, transcript, meta=None):
        self.calls.append(title)
        if self.fail:
            raise PublishError("сеть упала")
        return "https://example.com/doc"


def test_process_audio_writes_files_and_publishes(tmp_path):
    audio = tmp_path / "call.wav"
    audio.write_bytes(b"RIFF" + b"\x00" * 2000)
    fake_pub = FakePublisher()
    result = process_audio(
        audio, ScribeConfig(), title="Планёрка недели!",
        engine=FakeEngine(), publishers={"notion": fake_pub},
        out_root=tmp_path / "out",
    )
    assert result.published == {"notion": "https://example.com/doc"}
    assert fake_pub.calls == ["Планёрка недели!"]
    for key in ("md", "txt", "srt", "json"):
        assert result.files[key].is_file()
    assert "[01:15] Второй вопрос" in result.files["md"].read_text(encoding="utf-8")
    data = json.loads(result.files["json"].read_text(encoding="utf-8"))
    assert data["segments"][0]["text"] == "Привет всем"
    assert result.audio_path.parent == result.session_dir  # аудио скопировано рядом


def test_publish_error_does_not_lose_transcript(tmp_path):
    audio = tmp_path / "call.wav"
    audio.write_bytes(b"\x00" * 2000)
    result = process_audio(
        audio, ScribeConfig(), title="Созвон", engine=FakeEngine(),
        publishers={"notion": FakePublisher(fail=True)}, out_root=tmp_path / "out",
    )
    assert result.published == {}
    assert "notion" in result.publish_errors
    assert result.files["md"].is_file()


def test_slugify_keeps_cyrillic():
    assert slugify("Планёрка: итоги недели!") == "Планёрка_итоги_недели"


def test_load_config(tmp_path):
    cfg_file = tmp_path / "scribe.toml"
    cfg_file.write_text(
        'publish = ["notion"]\n[record]\nmic_device = "mic0"\n[transcribe]\n'
        'model = "medium"\nlanguage = "ru"\n',
        encoding="utf-8",
    )
    cfg = load_config(str(cfg_file))
    assert cfg.publish == ["notion"]
    assert cfg.record.mic_device == "mic0"
    assert cfg.transcribe.model == "medium"
    assert cfg.transcribe.language == "ru"

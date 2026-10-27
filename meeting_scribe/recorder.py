"""Запись звука созвона через ffmpeg.

Пишем ДВА входа и микшируем в один моно-WAV 16 kHz (идеально для Whisper):
ваш микрофон + системный звук (голоса собеседников).

Как получить «системный звук» зависит от ОС (подробно — в README):
- Windows: устройство «Стерео микшер / Stereo Mix» или VB-CABLE;
- macOS: виртуальное устройство BlackHole 2ch + Multi-Output Device;
- Linux: monitor-источник PulseAudio/PipeWire (``*.monitor``).

Список устройств: ``python -m meeting_scribe devices``
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .config import ConfigError, RecordConfig

_INSTALL_HINTS = {
    "windows": "winget install Gyan.FFmpeg  (или скачайте с ffmpeg.org)",
    "macos": "brew install ffmpeg",
    "linux": "sudo apt install ffmpeg  (или пакет вашего дистрибутива)",
}


def detect_os(name: str | None = None) -> str:
    name = name or sys.platform
    if name.startswith("win"):
        return "windows"
    if name == "darwin":
        return "macos"
    return "linux"


def ffmpeg_path() -> str:
    exe = shutil.which("ffmpeg")
    if not exe:
        os_name = detect_os()
        raise ConfigError(
            f"ffmpeg не найден в PATH. Установка ({os_name}): {_INSTALL_HINTS[os_name]}"
        )
    return exe


def _input_args(os_name: str, device: str) -> list[str]:
    if os_name == "windows":
        return ["-f", "dshow", "-i", f"audio={device}"]
    if os_name == "macos":
        # avfoundation: индекс аудиоустройства, формат ":<index>"
        return ["-f", "avfoundation", "-i", f":{device}"]
    return ["-f", "pulse", "-i", device]


def build_ffmpeg_command(
    cfg: RecordConfig,
    output: Path,
    os_name: str | None = None,
    max_seconds: float | None = None,
    ffmpeg: str = "ffmpeg",
) -> list[str]:
    """Собирает команду ffmpeg. Чистая функция — легко тестировать."""
    os_name = os_name or detect_os()
    devices = [d for d in (cfg.mic_device, cfg.system_device) if d]
    if not devices:
        raise ConfigError(
            "Не заданы аудиоустройства. Выполните `python -m meeting_scribe devices` "
            "и укажите mic_device / system_device в scribe.toml (секция [record])."
        )

    cmd: list[str] = [ffmpeg, "-hide_banner", "-loglevel", "error"]
    for dev in devices[:2]:
        cmd += _input_args(os_name, dev)

    if len(devices) >= 2:
        cmd += [
            "-filter_complex",
            "[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0:normalize=0[aout]",
            "-map",
            "[aout]",
        ]
    else:
        cmd += ["-map", "0:a"]

    if max_seconds:
        cmd += ["-t", str(int(max_seconds))]
    cmd += ["-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", "-y", str(output)]
    return cmd


def list_devices_command(os_name: str | None = None) -> tuple[list[str], str]:
    """Команда для списка устройств + подсказка, что искать в выводе."""
    os_name = os_name or detect_os()
    if os_name == "windows":
        return (
            ["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            "Ищите строки (audio): ваш микрофон и «Stereo Mix» / «CABLE Output (VB-Audio...)».",
        )
    if os_name == "macos":
        return (
            ["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""],
            "Секция AVFoundation audio devices: в конфиг пишется ИНДЕКС (число в скобках). "
            "Нужны микрофон и BlackHole 2ch.",
        )
    return (
        ["pactl", "list", "short", "sources"],
        "Микрофон — обычный source; системный звук — source с суффиксом .monitor. "
        "В конфиг пишется имя (вторая колонка).",
    )


class Recorder:
    """Обёртка над процессом ffmpeg с корректной остановкой.

    Остановка — отправкой ``q`` в stdin ffmpeg: он дописывает WAV-заголовок,
    файл остаётся валидным. Убивать процесс (SIGKILL) нельзя.
    """

    def __init__(self, cfg: RecordConfig):
        self.cfg = cfg
        self._proc: subprocess.Popen | None = None
        self.output: Path | None = None

    @property
    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def start(self, output: Path, max_seconds: float | None = None) -> Path:
        if self.is_running:
            raise RuntimeError("Запись уже идёт")
        output.parent.mkdir(parents=True, exist_ok=True)
        cmd = build_ffmpeg_command(
            self.cfg, output, max_seconds=max_seconds, ffmpeg=ffmpeg_path()
        )
        self._proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        self.output = output
        # ffmpeg падает сразу, если устройство недоступно — проверим.
        try:
            self._proc.wait(timeout=0.7)
        except subprocess.TimeoutExpired:
            return output  # процесс жив — запись пошла
        stderr = (self._proc.stderr.read() or b"").decode(errors="replace").strip()
        raise ConfigError(
            "ffmpeg завершился сразу после старта. Проверьте имена устройств "
            f"(`python -m meeting_scribe devices`).\n{stderr[:500]}"
        )

    def stop(self, timeout: float = 10.0) -> Path | None:
        if not self._proc:
            return self.output
        try:
            if self._proc.poll() is None:
                assert self._proc.stdin is not None
                self._proc.stdin.write(b"q\n")
                self._proc.stdin.flush()
                self._proc.wait(timeout=timeout)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        finally:
            self._proc = None
        return self.output

    def __enter__(self) -> "Recorder":
        return self

    def __exit__(self, *exc) -> None:
        self.stop()

# 🎙️ Meeting Scribe — локальный агент-стенографист созвонов

Агент живёт на **вашем** компьютере: во время созвона пишет микрофон + системный звук
(голоса собеседников), после — расшифровывает локально через Whisper и публикует
стенограмму с таймкодами в **Notion** и/или **Google Docs**. Бота-участника нет,
поэтому платформа созвона не важна: Google Meet, Zoom, Teams, Telegram, Телемост — что угодно.

```
календарь (.ics) ──▶ watch ──┐
                             ├─▶ Recorder (ffmpeg: микр. + системный звук -> wav 16kHz)
ручной запуск ─────▶ record ─┘            │
                                          ▼
                              faster-whisper (локально)
                                          ▼
                    recordings/<дата>_<время>_<название>/
                      transcript.md / .txt / .srt / .json  (+ audio.wav)
                                          ▼
                              Notion и/или Google Docs
```

⚖️ **Согласие участников.** Запись разговора без уведомления участников может быть
незаконна (152-ФЗ, GDPR) и нарушать политики платформ. Перед записью предупредите
собеседников — агент при каждом старте печати напоминает об этом, но ответственность за вами.

## Установка

Требуется Python 3.11+ и ffmpeg.

**Linux**
```bash
sudo apt install ffmpeg pulseaudio-utils   # pactl нужен для списка устройств
pip install -r meeting_scribe/requirements.txt
```

**macOS**
```bash
brew install ffmpeg blackhole-2ch
pip install -r meeting_scribe/requirements.txt
```

**Windows**
```powershell
winget install Gyan.FFmpeg
py -m pip install -r meeting_scribe\requirements.txt
```

Проверка окружения (честно покажет, чего не хватает):
```bash
python -m meeting_scribe check
```

## Настройка звука (самое важное)

Агент микширует два входа: **микрофон** и **системный звук**. Со вторым на каждой ОС по-своему.

**Windows.** Включите «Стерео микшер»: Параметры звука → Запись → ПКМ → «Показать отключённые
устройства» → Stereo Mix → Включить. Если такого устройства нет (зависит от звуковой карты),
поставьте бесплатный **VB-CABLE** (vb-audio.com): звук созвона направляется в `CABLE Input`,
агент пишет `CABLE Output`, а чтобы слышать самому — в свойствах `CABLE Output` (Запись)
включите «Прослушивать с данного устройства» → ваши наушники.

**macOS.** Системный звук напрямую писать нельзя, нужен **BlackHole 2ch** (уже поставили выше).
Откройте «Настройка Audio-MIDI» → «+» → «Создать многоканальное устройство вывода» (Multi-Output
Device): галочки на ваших наушниках/динамиках **и** BlackHole 2ch. Выберите это устройство как
системный выход. Тогда вы всё слышите, а агент пишет копию звука из BlackHole.

**Linux.** `pactl list short sources` — системный звук это источник с суффиксом `.monitor`
у вашего устройства вывода. Никаких драйверов не надо.

Затем:
```bash
python -m meeting_scribe devices      # список устройств с подсказкой
cp meeting_scribe/config.example.toml scribe.toml
# отредактируйте scribe.toml: [record] mic_device / system_device
```

## Использование

**Вручную** (начать в начале созвона, Ctrl+C в конце):
```bash
python -m meeting_scribe record --name "Планёрка"
python -m meeting_scribe record --name "Груминг" --duration 3600   # сам остановится через час
```

**Расшифровать уже имеющуюся запись** (zoom-рекординг, диктофон и т.п.):
```bash
python -m meeting_scribe transcribe meeting.mp4 --name "Созвон с клиентом"
```

**Автоматически по календарю** — агент следит за .ics-фидом и сам начинает/заканчивает запись:
```bash
python -m meeting_scribe watch
```
Как получить .ics-ссылку: Google Calendar → Настройки календаря → «Секретный адрес в формате iCal»;
Outlook → Опубликовать календарь → ссылка ICS; Яндекс Календарь → Экспорт. Вставьте в
`calendar.ics_source` в `scribe.toml`. Пишутся только события, похожие на созвоны
(ссылка Meet/Zoom/Teams/Телемост или слова из `calendar.keywords`), повторяющиеся события
(дейлики, WEEKLY/DAILY) поддерживаются. ⚠️ Секретная iCal-ссылка = доступ ко всему календарю:
не коммитьте `scribe.toml` (он уже в `.gitignore`).

Первый запуск скачает модель Whisper с HuggingFace (нужен интернет) и закеширует её.

| Модель | Размер | Скорость (CPU) | Качество для русского |
|---|---|---|---|
| tiny / base | 75–150 МБ | быстро | черновик, много ошибок |
| **small** (по умолчанию) | ~500 МБ | ~реальное время | приемлемо |
| medium | ~1.5 ГБ | 2–3× медленнее | хорошо |
| large-v3 | ~3 ГБ | медленно без GPU | лучше всего |

Меняется в `scribe.toml` → `transcribe.model`. Есть NVIDIA GPU — `device = "cuda"` ускорит в разы.

## Публикация в Notion

1. [notion.so/my-integrations](https://www.notion.so/my-integrations) → New integration → скопируйте секрет.
2. Задайте его как переменную окружения: `export NOTION_TOKEN=ntn_...` (Windows: `$env:NOTION_TOKEN="ntn_..."`).
3. Откройте страницу (или базу данных) «Стенограммы» → меню `…` → Connections → подключите интеграцию
   (без этого API вернёт 404 — Notion не показывает страницы интеграциям по умолчанию).
4. ID — 32-значный код из URL страницы/базы. Впишите в `scribe.toml` → `[notion]`
   ровно одно: `parent_page_id` (страница) или `database_id` (+ `title_property`, если колонка называется не `Name`).
5. `publish = ["notion"]` в том же файле.

## Публикация в Google Docs (опционально)

1. Google Cloud Console → проект → включить **Google Docs API** и **Google Drive API**.
2. IAM → Service Accounts → создать → Keys → скачать JSON-ключ.
3. `pip install google-api-python-client google-auth`
4. В `scribe.toml` → `[google_docs]`: `credentials_json` = путь к ключу, `share_with_email` = ваш e-mail
   (иначе документы сервисного аккаунта не появятся в вашем Drive — агент расшарит каждый вам).
5. `publish = ["google_docs"]` (можно вместе с Notion).

## Приватность и ограничения

- Запись и расшифровка — **полностью локально**. В сеть уходит только то, что вы сами настроили
  публиковать (Notion/Docs), либо аудио при `engine = "openai"`.
- Диаризации (кто именно сказал) пока нет — по вашему выбору «только текст с таймкодами».
  Кандидат на будущее: pyannote.
- Два созвона одновременно не пишутся (один микрофон и один системный звук на машину).
- Если компьютер уснул/выключился — запись прервётся; это плата за локальный подход без бота.
- Календарь: RRULE MONTHLY/YEARLY и EXDATE не разворачиваются (DAILY/WEEKLY — да).

## Разработка

```bash
pytest meeting_scribe/tests -q     # тесты без сети, ffmpeg и модели
```

Структура: `recorder.py` (ffmpeg), `transcribe.py` (faster-whisper/OpenAI), `pipeline.py`
(оркестрация), `calendar_watch.py` (ICS), `publishers/` (Notion, Google Docs),
`formatting.py` (md/txt/srt/json), `config.py` (TOML + env), `cli.py`.

Roadmap при желании: диаризация (pyannote), LLM-резюме и action items поверх стенограммы,
автостоп по тишине, системная служба/автозапуск `watch`.

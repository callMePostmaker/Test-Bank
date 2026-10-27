"""Публикация стенограммы в Notion.

Настройка (один раз):
1. notion.so/my-integrations -> New integration -> скопируйте секрет в NOTION_TOKEN.
2. Откройте страницу/базу, куда слать стенограммы: "..." -> Connections ->
   подключите вашу интеграцию (иначе API вернёт 404).
3. ID страницы/базы — 32-значный hex из URL — укажите в scribe.toml [notion].
"""

from __future__ import annotations

from ..formatting import fmt_duration, fmt_ts
from ..models import Transcript
from . import PublishError

API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
MAX_TEXT = 1900  # лимит Notion на один rich_text — 2000 символов
MAX_BLOCKS_PER_REQUEST = 100


def _rich_text(content: str, code: bool = False) -> dict:
    item = {"type": "text", "text": {"content": content}}
    if code:
        item["annotations"] = {"code": True}
    return item


def _paragraph(rich_text: list[dict]) -> dict:
    return {"object": "block", "type": "paragraph", "paragraph": {"rich_text": rich_text}}


def _chunk(text: str, size: int = MAX_TEXT) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]


def build_blocks(transcript: Transcript, meta: dict | None = None) -> list[dict]:
    """Сегменты -> блоки Notion: один абзац на сегмент, таймкод моноширинным."""
    meta = meta or {}
    blocks: list[dict] = [
        {
            "object": "block",
            "type": "heading_2",
            "heading_2": {"rich_text": [_rich_text("Стенограмма")]},
        }
    ]
    info = []
    if meta.get("date"):
        info.append(f"Дата: {meta['date']}")
    info.append(f"Длительность: {fmt_duration(transcript.duration)}")
    if transcript.language:
        info.append(f"Язык: {transcript.language}")
    blocks.append(_paragraph([_rich_text(" · ".join(info))]))
    blocks.append({"object": "block", "type": "divider", "divider": {}})

    if not transcript.segments:
        blocks.append(_paragraph([_rich_text("(речь не распознана)")]))
    for seg in transcript.segments:
        ts = _rich_text(f"[{fmt_ts(seg.start)}] ", code=True)
        for j, part in enumerate(_chunk(seg.text.strip())):
            rich = ([ts] if j == 0 else []) + [_rich_text(part)]
            blocks.append(_paragraph(rich))
    return blocks


class NotionPublisher:
    def __init__(
        self,
        token: str,
        parent_page_id: str | None = None,
        database_id: str | None = None,
        title_property: str = "Name",
        session=None,
    ):
        if not token:
            raise PublishError("Не задан NOTION_TOKEN")
        if bool(parent_page_id) == bool(database_id):
            raise PublishError(
                "Укажите ровно одно: notion.parent_page_id или notion.database_id в конфиге"
            )
        self.parent_page_id = parent_page_id
        self.database_id = database_id
        self.title_property = title_property
        if session is None:
            import requests

            session = requests.Session()
        self.session = session
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    def _post(self, url: str, payload: dict) -> dict:
        resp = self.session.post(url, headers=self.headers, json=payload, timeout=60)
        if resp.status_code >= 400:
            raise PublishError(f"Notion API {resp.status_code}: {resp.text[:400]}")
        return resp.json()

    def _patch(self, url: str, payload: dict) -> dict:
        resp = self.session.patch(url, headers=self.headers, json=payload, timeout=60)
        if resp.status_code >= 400:
            raise PublishError(f"Notion API {resp.status_code}: {resp.text[:400]}")
        return resp.json()

    def publish(self, title: str, transcript: Transcript, meta: dict | None = None) -> str:
        """Создаёт страницу со стенограммой, возвращает её URL."""
        blocks = build_blocks(transcript, meta)
        first, rest = blocks[:MAX_BLOCKS_PER_REQUEST], blocks[MAX_BLOCKS_PER_REQUEST:]

        if self.database_id:
            parent = {"database_id": self.database_id}
            properties = {self.title_property: {"title": [_rich_text(title)]}}
        else:
            parent = {"page_id": self.parent_page_id}
            properties = {"title": [_rich_text(title)]}

        page = self._post(
            f"{API}/pages",
            {"parent": parent, "properties": properties, "children": first},
        )
        page_id = page["id"]
        # Остаток блоков дозаписываем пачками по 100 (лимит API).
        for i in range(0, len(rest), MAX_BLOCKS_PER_REQUEST):
            batch = rest[i : i + MAX_BLOCKS_PER_REQUEST]
            self._patch(f"{API}/blocks/{page_id}/children", {"children": batch})
        return page.get("url", f"https://www.notion.so/{page_id.replace('-', '')}")

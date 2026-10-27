"""Публикация стенограммы наружу: Notion, Google Docs.

Локальные файлы (.md/.txt/.srt/.json) пишутся всегда — публикация
является дополнением, её ошибка не теряет стенограмму.
"""

from __future__ import annotations

from ..config import ConfigError, ScribeConfig


class PublishError(RuntimeError):
    pass


def build_publishers(cfg: ScribeConfig) -> dict:
    """Собирает публикаторы по конфигу: {"notion": NotionPublisher, ...}."""
    publishers = {}
    for name in cfg.publish:
        if name == "notion":
            from .notion import NotionPublisher

            if not cfg.notion_token:
                raise ConfigError(
                    "Для публикации в Notion задайте переменную NOTION_TOKEN "
                    "(токен интеграции: notion.so/my-integrations)"
                )
            publishers["notion"] = NotionPublisher(
                token=cfg.notion_token,
                parent_page_id=cfg.notion.parent_page_id or None,
                database_id=cfg.notion.database_id or None,
                title_property=cfg.notion.title_property,
            )
        elif name == "google_docs":
            from .google_docs import GoogleDocsPublisher

            publishers["google_docs"] = GoogleDocsPublisher(
                credentials_json=cfg.google_docs.credentials_json,
                folder_id=cfg.google_docs.folder_id or None,
                share_with_email=cfg.google_docs.share_with_email or None,
            )
        else:
            raise ConfigError(f"Неизвестный публикатор {name!r}. Допустимо: notion, google_docs")
    return publishers

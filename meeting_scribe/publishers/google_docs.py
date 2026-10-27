"""Публикация стенограммы в Google Docs (опционально, через сервисный аккаунт).

Настройка (один раз):
1. Google Cloud Console -> проект -> включить Google Docs API и Google Drive API.
2. IAM -> Service Accounts -> создать аккаунт -> Keys -> JSON-ключ скачать.
3. Путь к JSON указать в scribe.toml [google_docs] credentials_json,
   а share_with_email — ваш e-mail: документы сервисного аккаунта иначе
   не видны в вашем Drive, агент расшарит каждый созданный документ вам.

Зависимости: pip install google-api-python-client google-auth
"""

from __future__ import annotations

from pathlib import Path

from ..formatting import to_text
from ..models import Transcript
from . import PublishError

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]
CHUNK = 40_000  # символов на один insertText


class GoogleDocsPublisher:
    def __init__(
        self,
        credentials_json: str,
        folder_id: str | None = None,
        share_with_email: str | None = None,
    ):
        if not credentials_json or not Path(credentials_json).is_file():
            raise PublishError(
                "google_docs.credentials_json не задана или файл не найден (см. README)"
            )
        self.credentials_json = credentials_json
        self.folder_id = folder_id
        self.share_with_email = share_with_email
        self._docs = None
        self._drive = None

    def _services(self):
        if self._docs is None:
            try:
                from google.oauth2 import service_account
                from googleapiclient.discovery import build
            except ImportError as exc:
                raise PublishError(
                    "Для Google Docs установите: pip install google-api-python-client google-auth"
                ) from exc
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_json, scopes=SCOPES
            )
            self._docs = build("docs", "v1", credentials=creds)
            self._drive = build("drive", "v3", credentials=creds)
        return self._docs, self._drive

    def publish(self, title: str, transcript: Transcript, meta: dict | None = None) -> str:
        docs, drive = self._services()
        meta_file = {"name": title, "mimeType": "application/vnd.google-apps.document"}
        if self.folder_id:
            meta_file["parents"] = [self.folder_id]
        created = drive.files().create(body=meta_file, fields="id,webViewLink").execute()
        doc_id = created["id"]

        text = to_text(transcript) or "(речь не распознана)"
        # Вставляем кусками с конца документа (endOfSegmentLocation = append).
        for i in range(0, len(text), CHUNK):
            chunk = text[i : i + CHUNK]
            docs.documents().batchUpdate(
                documentId=doc_id,
                body={
                    "requests": [
                        {"insertText": {"endOfSegmentLocation": {}, "text": chunk}}
                    ]
                },
            ).execute()

        if self.share_with_email:
            drive.permissions().create(
                fileId=doc_id,
                body={
                    "type": "user",
                    "role": "writer",
                    "emailAddress": self.share_with_email,
                },
                sendNotificationEmail=False,
            ).execute()
        return created.get("webViewLink", f"https://docs.google.com/document/d/{doc_id}")

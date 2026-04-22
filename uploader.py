from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from config import Settings


LOGGER = logging.getLogger(__name__)


class YouTubeUploader:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def is_configured(self) -> bool:
        return bool(
            self.settings.bhakti_youtube_client_secret_file
            and self.settings.bhakti_youtube_token_file
        )

    def upload(self, video_path: Path, seo: dict[str, Any], publish_at: str | None = None) -> dict[str, Any]:
        if not self.is_configured():
            return {
                "status": "skipped",
                "reason": "YouTube OAuth files are not configured yet.",
                "video_path": str(video_path),
            }

        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
        except ImportError:
            return {
                "status": "skipped",
                "reason": "YouTube upload dependencies are not installed.",
                "video_path": str(video_path),
            }

        scopes = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"]
        token_path = Path(self.settings.bhakti_youtube_token_file)
        credentials = None
        if token_path.exists():
            credentials = Credentials.from_authorized_user_file(str(token_path), scopes)
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.settings.bhakti_youtube_client_secret_file,
                    scopes,
                )
                credentials = flow.run_local_server(port=0)
            token_path.write_text(credentials.to_json(), encoding="utf-8")

        youtube = build("youtube", "v3", credentials=credentials)
        
        status_body = {
            "privacyStatus": "private" if publish_at else "public",
            "selfDeclaredMadeForKids": False,
        }
        if publish_at:
            # YouTube expects ISO 8601 with timezone (e.g. Z or +05:30)
            if "Z" in publish_at or "+" in publish_at or "-" in publish_at:
                status_body["publishAt"] = publish_at
            else:
                # Fallback for old format or missing offset
                status_body["publishAt"] = f"{publish_at}:00Z"

        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": seo["title"],
                    "description": seo["description"],
                    "tags": seo.get("tags", []),
                    "categoryId": self.settings.youtube_category_id or "27",
                    "defaultLanguage": "hi",
                    "defaultAudioLanguage": "hi",
                },
                "status": status_body,
            },
            media_body=MediaFileUpload(str(video_path), chunksize=-1, resumable=True),
        )
        response = request.execute()
        LOGGER.info("Uploaded video to YouTube with id %s", response.get("id"))
        return {
            "status": "uploaded",
            "video_id": response.get("id"),
            "response": response,
        }

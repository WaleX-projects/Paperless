"""Optional MongoDB store for raw AI responses (audit/debug). No-op if MONGO_URL unset."""
from datetime import datetime
from .config import settings

_col = None
if settings.mongo_url:
    from pymongo import MongoClient
    _col = MongoClient(settings.mongo_url)["grader"]["ai_responses"]


def save_raw(submission_id: int, payload: dict) -> None:
    if _col is not None:
        _col.insert_one({"submission_id": submission_id, "payload": payload, "at": datetime.utcnow()})

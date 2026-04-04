import uuid
import logging
import pandas as pd
import time
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class SessionStore:
    def __init__(self):
        self._store: Dict[str, Dict] = {}

    def save(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        session_id = str(uuid.uuid4())[:8]
        self._store[session_id] = {
            "df": df,
            "metadata": metadata,
            "created_at": time.time()
        }
        logger.info(f"Session '{session_id}' saved — {len(df)} rows")
        return session_id

    def get(self, session_id: str) -> Optional[Tuple[pd.DataFrame, Dict[str, Any]]]:
        entry = self._store.get(session_id)
        if not entry:
            logger.warning(f"Session '{session_id}' not found")
            return None
        return entry["df"], entry["metadata"]

    def delete(self, session_id: str):
        self._store.pop(session_id, None)

    def cleanup(self, max_age_seconds: int = 3600):
        now = time.time()
        self._store = {
            sid: data
            for sid, data in self._store.items()
            if now - data["created_at"] < max_age_seconds
        }

    def count(self) -> int:
        return len(self._store)


# Shared instance
session_store = SessionStore()
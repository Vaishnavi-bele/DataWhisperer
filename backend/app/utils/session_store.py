import uuid
import pandas as pd
from typing import Dict, Any, Optional, Tuple

SessionData = Tuple[pd.DataFrame, Dict[str, Any]]

class SessionStore:
    def __init__(self):
        self._store: Dict[str, Dict] = {}

    def save(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        while True:
            sid = str(uuid.uuid4())[:8]
            if sid not in self._store:
                break
        self._store[sid] = {"df": df, "metadata": metadata}
        return sid

    def get(self, sid: str) -> Optional[SessionData]:
        entry = self._store.get(sid)
        if not entry:
            return None
        return entry["df"], entry["metadata"]

    def count(self) -> int:
        return len(self._store)

session_store = SessionStore()
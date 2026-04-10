import re
import logging
from typing import Tuple, List

logger = logging.getLogger(__name__)


class SQLGenerator:

    def generate(self, question: str, schema: dict) -> Tuple[str, str]:
        q = question.lower().strip()

        cols = list(schema.keys())

        num_cols = [c for c, t in schema.items()
                    if any(x in t for x in ["int", "float", "double", "numeric", "decimal"])]

        cat_cols = [c for c, t in schema.items()
                    if "object" in t or "str" in t]

        mentioned = self._find_mentioned_columns(q, cols)
        intent = self._detect_intent(q)

        print(f"🔥 Intent: {intent} | Mentioned: {mentioned}")

        sql = self._build_sql(q, intent, mentioned, num_cols, cat_cols)
        explanation = f"Intent detected: {intent}"

        return sql, explanation

    # -------------------------
    # COLUMN DETECTION
    # -------------------------
    def _find_mentioned_columns(self, question: str, cols: List[str]) -> List[str]:
        found = []
        q = question.replace("_", " ").lower()

        for col in cols:
            readable = col.replace("_", " ").lower()
            if readable in q:
                found.append(col)

        return found

    # -------------------------
    # INTENT DETECTION
    # -------------------------
    def _detect_intent(self, q: str) -> str:
        if re.search(r"\btop\s+\d+\b", q):
            return "top_n"

        if any(w in q for w in ["count", "how many"]):
            return "count"

        if any(w in q for w in ["average", "avg", "mean"]):
            return "average"

        if any(w in q for w in ["total", "sum"]):
            return "sum"

        if any(w in q for w in ["by", "group"]):
            return "group"

        return "select"

    # -------------------------
    # SMART COLUMN SELECTION 🔥
    # -------------------------
    def _best_num_col(self, mentioned, num_cols, question):
        q = question.lower()

        # 1. direct mention
        for col in mentioned:
            if col in num_cols:
                return col

        # 2. keyword mapping
        keyword_map = {
            "revenue": ["revenue", "sales", "amount", "income"],
            "quantity": ["quantity", "qty", "units", "count"],
            "price": ["price", "cost"]
        }

        for col in num_cols:
            col_lower = col.lower()
            for key, words in keyword_map.items():
                if any(w in q for w in words) and key in col_lower:
                    return col

        # 3. fallback
        return num_cols[0] if num_cols else None

    def _best_cat_col(self, mentioned, cat_cols):
        for col in mentioned:
            if col in cat_cols:
                return col
        return cat_cols[0] if cat_cols else None

    # -------------------------
    # SQL BUILDER
    # -------------------------
    def _build_sql(self, q, intent, mentioned, num_cols, cat_cols):

        num_col = self._best_num_col(mentioned, num_cols, q)
        cat_col = self._best_cat_col(mentioned, cat_cols)

        # TOP N
        top_match = re.search(r"\btop\s+(\d+)\b", q)
        if intent == "top_n" and top_match:
            n = top_match.group(1)

            if num_col and cat_col:
                return f"SELECT {cat_col}, SUM({num_col}) as total FROM data GROUP BY {cat_col} ORDER BY total DESC LIMIT {n}"

            if num_col:
                return f"SELECT * FROM data ORDER BY {num_col} DESC LIMIT {n}"

        # COUNT
        if intent == "count":
            if cat_col:
                return f"SELECT {cat_col}, COUNT(*) as count FROM data GROUP BY {cat_col} ORDER BY count DESC"
            return "SELECT COUNT(*) as total FROM data"

        # AVERAGE
        if intent == "average":
            if num_col:
                return f"SELECT AVG({num_col}) as average FROM data"

        # SUM
        if intent == "sum":
            if num_col and cat_col:
                return f"SELECT {cat_col}, SUM({num_col}) as total FROM data GROUP BY {cat_col}"
            if num_col:
                return f"SELECT SUM({num_col}) as total FROM data"

        # GROUP
        if intent == "group":
            if num_col and cat_col:
                return f"SELECT {cat_col}, SUM({num_col}) as total FROM data GROUP BY {cat_col}"

        # DEFAULT
        return "SELECT * FROM data LIMIT 20"
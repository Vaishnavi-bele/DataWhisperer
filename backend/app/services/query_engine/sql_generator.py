"""
SQL Generator (Final Polished Version)
"""

import re
import logging
from typing import Tuple, Dict, List, Optional

logger = logging.getLogger(__name__)

PROMPT = """Convert the question to a SQLite SQL query.

Table name: data
Columns: {columns}

Rules:
- Only SELECT queries
- Use ONLY given columns
- Table name is always 'data'
- Add LIMIT 100 unless aggregation

Question: {question}

SQL:
"""


class SQLGenerator:
    def __init__(self):
        self._pipe = None
        self._rb = _RuleBasedEngine()

    def generate(self, question: str, schema: Dict[str, str]) -> Tuple[str, str]:
        try:
            sql = self._flan(question, schema)
            if sql and self._is_safe(sql):
                return sql, "AI-generated"
        except Exception as e:
            logger.warning(f"Flan failed: {e}")

        return self._rb.generate(question, schema)

    def _flan(self, question, schema):
        pipe = self._load()
        cols = ", ".join(f"{c}({t[:5]})" for c, t in schema.items())
        prompt = PROMPT.format(columns=cols, question=question)
        out = pipe(prompt, max_new_tokens=150, do_sample=False)[0]["generated_text"]
        return self._clean(out)

    def _load(self):
        if self._pipe is None:
            from transformers import pipeline
            self._pipe = pipeline("text2text-generation", model="google/flan-t5-base")
        return self._pipe

    def _clean(self, raw):
        raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
        raw = raw.replace("`", "").strip()
        for line in raw.splitlines():
            if line.upper().startswith("SELECT"):
                return line
        return None

    def _is_safe(self, sql):
        blocked = ["DROP", "DELETE", "UPDATE", "INSERT"]
        s = sql.upper()
        return s.startswith("SELECT") and not any(b in s for b in blocked)


# ───────────────── RULE ENGINE ─────────────────
class _RuleBasedEngine:

    INTENTS = {
        "top_n": [r"\btop\s+\d+"],
        "bottom_n": [r"\bbottom\s+\d+"],
        "count": [r"\bcount\b", r"\bhow many\b"],
        "average": [r"\bavg\b", r"\baverage\b"],
        "sum": [r"\btotal\b", r"\bsum\b"],
        "compare": [r"\bvs\b", r"\bversus\b"],
        "high": [r"\bhigh\b", r"\bhighest\b"],
        "low": [r"\blow\b", r"\blowest\b"],
    }

    def generate(self, question: str, schema: Dict[str, str]) -> Tuple[str, str]:

        q = question.lower()
        num_cols = [c for c, t in schema.items() if "int" in t or "float" in t]
        cat_cols = [c for c, t in schema.items() if "object" in t]

        intent = self._intent(q)
        mentioned = [c for c in schema if c.lower() in q]

        num = self._best_num(mentioned, num_cols)
        cat = self._best_cat(mentioned, cat_cols)
        n = self._limit(q)

        # COMPARE
        if intent == "compare":
            parts = re.split(r"\bvs\b|\bversus\b", q)
            if len(parts) >= 2:
                c1 = self._match(parts[0], schema)
                c2 = self._match(parts[1], schema)
                if c1 and c2:
                    return f"SELECT {c1}, {c2} FROM data LIMIT 100", "compare"

        # TOP / BOTTOM
        if intent in ("top_n", "bottom_n") and num:
            order = "DESC" if intent == "top_n" else "ASC"
            return f"SELECT * FROM data ORDER BY {num} {order} LIMIT {n}", intent

        # HIGH / LOW
        if intent in ("high", "low") and num:
            order = "DESC" if intent == "high" else "ASC"
            return f"SELECT {cat}, {num} FROM data ORDER BY {num} {order} LIMIT {n}", intent

        # AGGREGATES
        if intent == "count":
            return "SELECT COUNT(*) as total FROM data", "count"

        if intent == "average" and num:
            return f"SELECT AVG({num}) FROM data", "avg"

        if intent == "sum" and num:
            return f"SELECT SUM({num}) FROM data", "sum"

        return f"SELECT * FROM data LIMIT {n}", "fallback"

    # ─ helpers ─
    def _intent(self, q):
        for k, patterns in self.INTENTS.items():
            for p in patterns:
                if re.search(p, q):
                    return k
        return "fallback"

    def _limit(self, q, default=10, max_limit=100):
        m = re.search(r"\d+", q)
        return min(int(m.group()), max_limit) if m else default

    def _best_num(self, mentioned, num_cols):
        for c in mentioned:
            if c in num_cols:
                return c
        for k in ["profit", "revenue", "sales", "amount", "price"]:
            for c in num_cols:
                if k in c:
                    return c
        return num_cols[0] if num_cols else None

    def _best_cat(self, mentioned, cat_cols):
        for c in mentioned:
            if c in cat_cols:
                return c
        return cat_cols[0] if cat_cols else None

    def _match(self, text, schema):
        for c in schema:
            if c.lower() in text:
                return c
        return None
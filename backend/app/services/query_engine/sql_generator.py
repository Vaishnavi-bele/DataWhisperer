import re
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

PROMPT_TEMPLATE = """Convert this question to a SQLite SQL query.
Table name: data
Columns: {columns}
Question: {question}
Rules:
- Use only SELECT statements
- Use only the columns listed above
- Add LIMIT 100 unless user asks for more
- For top N questions use ORDER BY ... DESC LIMIT N
SQL:"""


class SQLGenerator:
    def __init__(self, use_llm: bool = False):
        self._pipeline = None
        self.use_llm = use_llm  # control LLM usage

    def _get_pipeline(self):
        """Lazy load LLM model"""
        if self._pipeline is None:
            from transformers import pipeline
            logger.info("Loading Flan-T5 model...")
            self._pipeline = pipeline(
                "text2text-generation",
                model="google/flan-t5-base",
                max_new_tokens=150,
            )
            logger.info("✅ Model loaded")
        return self._pipeline

    def generate(self, question: str, schema: Dict[str, str]) -> Tuple[str, str]:
        """
        Returns (sql, explanation)
        """

        # Try LLM if enabled
        if self.use_llm:
            try:
                sql = self._generate_with_llm(question, schema)
            except Exception as e:
                logger.warning(f"LLM failed: {e}")
                sql = self._fallback_sql(question, schema)
        else:
            sql = self._fallback_sql(question, schema)

        # Final cleaning + safety
        sql = self._clean_sql(sql)
        sql = self._ensure_safe(sql)

        explanation = self._explain(question)

        logger.info(f"Final SQL: {sql}")
        return sql, explanation

    def _generate_with_llm(self, question: str, schema: Dict[str, str]) -> str:
        columns_str = ", ".join(f"{col} ({dtype})" for col, dtype in schema.items())

        prompt = PROMPT_TEMPLATE.format(
            columns=columns_str,
            question=question,
        )

        pipe = self._get_pipeline()
        result = pipe(prompt)[0]["generated_text"].strip()

        return result

    def _clean_sql(self, raw: str) -> str:
        raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
        raw = raw.replace("`", "").strip()

        for line in raw.split("\n"):
            line = line.strip()
            if line.upper().startswith("SELECT"):
                return line

        return raw

    def _ensure_safe(self, sql: str) -> str:
        """Ensure query is safe"""
        sql_upper = sql.upper()

        # Block dangerous queries
        for bad in ["DROP", "DELETE", "UPDATE", "INSERT"]:
            if bad in sql_upper:
                raise ValueError("Unsafe SQL detected")

        # Ensure SELECT
        if not sql_upper.startswith("SELECT"):
            raise ValueError("Only SELECT queries are allowed")

        # Add LIMIT if missing
        if "LIMIT" not in sql_upper:
            sql += " LIMIT 100"

        return sql

    def _fallback_sql(self, question: str, schema: Dict[str, str]) -> str:
        """Rule-based SQL generator"""
        q = question.lower()
        cols = list(schema.keys())

        num_cols = [
            c for c, t in schema.items()
            if any(x in t.lower() for x in ["int", "float", "double"])
        ]

        cat_cols = [c for c in cols if c not in num_cols]

        # Top N
        top_match = re.search(r"top\s+(\d+)", q)
        if top_match and num_cols:
            n = top_match.group(1)
            return f"SELECT * FROM data ORDER BY {num_cols[0]} DESC LIMIT {n}"

        # Count
        if "count" in q or "how many" in q:
            if cat_cols:
                return f"SELECT {cat_cols[0]}, COUNT(*) as count FROM data GROUP BY {cat_cols[0]} ORDER BY count DESC"
            return "SELECT COUNT(*) as total_rows FROM data"

        # Average
        if any(word in q for word in ["average", "avg", "mean"]):
            if num_cols:
                return f"SELECT AVG({num_cols[0]}) as average_{num_cols[0]} FROM data"

        # Sum / Total
        if any(word in q for word in ["sum", "total"]):
            if num_cols and cat_cols:
                return f"SELECT {cat_cols[0]}, SUM({num_cols[0]}) as total FROM data GROUP BY {cat_cols[0]} ORDER BY total DESC"
            if num_cols:
                return f"SELECT SUM({num_cols[0]}) as total FROM data"

        # Default
        return "SELECT * FROM data LIMIT 20"

    def _explain(self, question: str) -> str:
        return f"The system generated a SQL query to answer: \"{question}\""
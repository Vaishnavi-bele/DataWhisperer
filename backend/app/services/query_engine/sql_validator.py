import re
import logging
import sqlite3
import pandas as pd
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

BLOCKED = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "TRUNCATE", "EXEC", "ATTACH", "PRAGMA"]


class SQLValidator:

    def validate(self, sql: str) -> Tuple[bool, Optional[str]]:
        sql_upper = sql.upper().strip()

        if not sql_upper.startswith("SELECT"):
            return False, "Only SELECT queries are allowed."

        for keyword in BLOCKED:
            if re.search(rf"\b{keyword}\b", sql_upper):
                return False, f"Blocked keyword: {keyword}"

        return True, None

    def execute(self, sql: str, df: pd.DataFrame) -> Tuple[pd.DataFrame, str]:
        # Clean SQL
        sql = sql.strip().rstrip(";")

        is_valid, error = self.validate(sql)
        if not is_valid:
            raise ValueError(f"SQL validation failed: {error}")

        # Add LIMIT if missing
        if "LIMIT" not in sql.upper():
            sql += " LIMIT 100"

        logger.info(f"Executing SQL: {sql}")

        conn = sqlite3.connect(":memory:")
        try:
            df.to_sql("data", conn, index=False, if_exists="replace")
            result = pd.read_sql_query(sql, conn)
            return result, f"Returned {len(result)} rows."
        except Exception as e:
            raise ValueError(self._friendly_error(str(e), df))
        finally:
            conn.close()

    def _friendly_error(self, raw: str, df: pd.DataFrame) -> str:
        raw_lower = raw.lower()

        if "no such column" in raw_lower:
            match = re.search(r"no such column: (.+)", raw, re.IGNORECASE)
            bad = match.group(1).strip() if match else "unknown"
            available = ", ".join(df.columns[:10].tolist())
            return f"Column '{bad}' not found. Available columns: {available}"

        if "no such table" in raw_lower:
            return "Table not found. Please upload data first."

        if "syntax error" in raw_lower:
            return "SQL syntax error. Try rephrasing your question."

        return f"Query failed: {raw}"
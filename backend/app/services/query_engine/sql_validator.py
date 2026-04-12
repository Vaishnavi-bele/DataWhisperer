import re
import sqlite3
import pandas as pd

BLOCKED = ["DROP","DELETE","INSERT","UPDATE","ALTER","CREATE"]

class SQLValidator:

    def validate(self, sql: str):
        u = sql.upper().strip()

        if not u.startswith("SELECT"):
            return False, "Only SELECT queries allowed."

        for kw in BLOCKED:
            if re.search(rf"\b{kw}\b", u):
                return False, f"Blocked keyword: {kw}"

        return True, None

    def execute(self, sql: str, df: pd.DataFrame):
        ok, err = self.validate(sql)
        if not ok:
            raise ValueError(err)

        # LIMIT safety
        if "LIMIT" not in sql.upper():
            sql = sql.rstrip(";") + " LIMIT 100"

        conn = sqlite3.connect(":memory:")

        try:
            df.to_sql("data", conn, index=False, if_exists="replace")
            result = pd.read_sql_query(sql, conn)

            if len(result) > 1000:
                result = result.head(1000)

            return result, f"{len(result)} rows returned"

        finally:
            conn.close()
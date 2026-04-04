import logging
import pandas as pd

logger = logging.getLogger(__name__)


class InsightGenerator:
    def __init__(self):
        self._pipeline = None  # lazy load (future use)

    def generate(self, question: str, df: pd.DataFrame) -> str:
        if df is None or df.empty:
            return "The query returned no results. Try a different question."

        return self._rule_based(question, df)

    def _rule_based(self, question: str, df: pd.DataFrame) -> str:
        num_cols = list(df.select_dtypes(include="number").columns)
        cat_cols = list(df.select_dtypes(include="object").columns)

        rows = len(df)
        parts = [f"Your query returned {rows} row{'s' if rows != 1 else ''}."]

        # Numeric insights (top 2 columns)
        for col in num_cols[:2]:
            total = df[col].sum()
            avg = df[col].mean()
            maximum = df[col].max()
            minimum = df[col].min()

            parts.append(
                f"For '{col}': total = {total:,.2f}, "
                f"average = {avg:,.2f}, "
                f"max = {maximum:,.2f}, "
                f"min = {minimum:,.2f}."
            )

        # Categorical insight
        if cat_cols:
            top_value = df[cat_cols[0]].mode().iloc[0] if not df[cat_cols[0]].mode().empty else None
            if top_value:
                parts.append(f"Most frequent '{cat_cols[0]}' is '{top_value}'.")

        # Ranking insight (if sorted)
        if num_cols and rows > 0:
            top_row = df.iloc[0]
            parts.append(f"Top record has {num_cols[0]} = {top_row[num_cols[0]]:,.2f}.")

        # Size insight
        if rows == 1:
            parts.append("Single result found.")
        elif rows > 50:
            parts.append("Large result set — consider filtering further.")

        return " ".join(parts)
import logging
import pandas as pd
import plotly.express as px
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class ChartSelector:

    def select_and_build(self, df: pd.DataFrame, question: str) -> Tuple[str, Optional[str]]:
        if df is None or df.empty:
            return "table", None

        # limit for performance
        if len(df) > 1000:
            df = df.head(1000)

        chart_type = self._decide(df, question)
        fig = self._build(df, chart_type, question)

        return chart_type, (fig.to_json() if fig else None)

    # ───────────────── DECISION ENGINE ─────────────────
    def _decide(self, df: pd.DataFrame, question: str) -> str:
        q = question.lower()

        num_cols = list(df.select_dtypes(include="number").columns)
        cat_cols = list(df.select_dtypes(include="object").columns)

        if any(w in q for w in ["trend", "over time", "monthly", "daily"]):
            return "line"

        if any(w in q for w in ["distribution", "spread", "histogram"]):
            return "histogram"

        if any(w in q for w in ["percentage", "share", "proportion"]):
            return "pie"

        if num_cols and cat_cols:
            if len(df) <= 8:
                return "pie"
            return "bar"

        if len(num_cols) >= 2:
            return "scatter"

        if len(num_cols) == 1:
            return "histogram"

        return "table"

    # ───────────────── BUILD CHART ─────────────────
    def _build(self, df: pd.DataFrame, chart_type: str, question: str):

        num_cols = list(df.select_dtypes(include="number").columns)
        cat_cols = list(df.select_dtypes(include="object").columns)

        try:
            if chart_type == "bar" and num_cols and cat_cols:
                return px.bar(df, x=cat_cols[0], y=num_cols[0], title=question)

            elif chart_type == "line" and num_cols:
                x = cat_cols[0] if cat_cols else df.columns[0]
                return px.line(df, x=x, y=num_cols[0], title=question)

            elif chart_type == "pie" and num_cols and cat_cols:
                return px.pie(df, names=cat_cols[0], values=num_cols[0], title=question)

            elif chart_type == "scatter" and len(num_cols) >= 2:
                return px.scatter(df, x=num_cols[0], y=num_cols[1], title=question)

            elif chart_type == "histogram" and num_cols:
                return px.histogram(df, x=num_cols[0], title=question)

            return None

        except Exception as e:
            logger.warning(f"Chart build failed: {e}")
            return None
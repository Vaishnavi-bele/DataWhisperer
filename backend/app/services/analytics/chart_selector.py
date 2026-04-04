import logging
import pandas as pd
import plotly.express as px
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#a78bfa"]


class ChartSelector:

    def select_and_build(self, df: pd.DataFrame, question: str) -> Tuple[str, Optional[str]]:
        if df is None or df.empty:
            return "table", None

        df = df.head(50)  # limit for performance

        chart_type = self._decide(df, question)
        fig = self._build(df, chart_type, question)

        if fig is None:
            return "table", None

        return chart_type, fig.to_json()

    def _decide(self, df: pd.DataFrame, question: str) -> str:
        q = question.lower()

        num_cols = list(df.select_dtypes(include="number").columns)
        cat_cols = list(df.select_dtypes(include="object").columns)

        # Time detection
        if any("date" in col.lower() or "time" in col.lower() for col in df.columns):
            return "line"

        if any(w in q for w in ["trend", "over time", "monthly", "yearly", "daily"]):
            return "line"

        if any(w in q for w in ["proportion", "share", "percentage", "breakdown"]):
            return "pie"

        if any(w in q for w in ["distribution", "histogram", "spread"]):
            return "histogram"

        if num_cols and cat_cols and len(df) <= 8:
            return "pie"

        if num_cols and cat_cols:
            return "bar"

        if len(num_cols) >= 2:
            return "scatter"

        if len(num_cols) == 1:
            return "histogram"

        return "table"

    def _build(self, df: pd.DataFrame, chart_type: str, question: str):
        num_cols = list(df.select_dtypes(include="number").columns)
        cat_cols = list(df.select_dtypes(include="object").columns)

        title = question.capitalize()

        try:
            # Sort for better visuals
            if num_cols:
                df = df.sort_values(by=num_cols[0], ascending=False)

            if chart_type == "bar" and num_cols and cat_cols:
                fig = px.bar(df, x=cat_cols[0], y=num_cols[0], title=title,
                             color_discrete_sequence=COLORS, text_auto=True)

            elif chart_type == "line" and num_cols:
                x = cat_cols[0] if cat_cols else df.columns[0]
                fig = px.line(df, x=x, y=num_cols[0], title=title,
                              color_discrete_sequence=COLORS, markers=True)

            elif chart_type == "pie" and num_cols and cat_cols:
                fig = px.pie(df, names=cat_cols[0], values=num_cols[0],
                             title=title, color_discrete_sequence=COLORS, hole=0.35)

            elif chart_type == "scatter" and len(num_cols) >= 2:
                fig = px.scatter(df, x=num_cols[0], y=num_cols[1],
                                 title=title, color_discrete_sequence=COLORS)

            elif chart_type == "histogram" and num_cols:
                fig = px.histogram(df, x=num_cols[0], title=title,
                                   color_discrete_sequence=COLORS, nbins=20)

            else:
                return None

            fig.update_layout(
                paper_bgcolor="#0f1117",
                plot_bgcolor="#0f1117",
                font=dict(color="#e2e8f0", size=12),
                title_font=dict(size=14, color="#a5b4fc"),
                margin=dict(l=40, r=40, t=50, b=40),
                xaxis=dict(gridcolor="#1e2233"),
                yaxis=dict(gridcolor="#1e2233"),
            )

            return fig

        except Exception as e:
            logger.warning(f"Chart failed: {e}", exc_info=True)
            return None
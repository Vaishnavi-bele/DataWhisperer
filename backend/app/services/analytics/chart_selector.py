"""
DataWhisperer - Smart Chart Selector
=====================================
Picks the BEST chart type based on:
  1. Question keywords  (what the user asked)
  2. Data shape         (rows x cols)
  3. Column types       (numeric vs categorical vs date)
  4. Result size        (1 row, few rows, many rows)

Chart types supported:
  bar       - compare categories
  line      - trends over time
  pie       - proportions / shares (<=8 groups)
  scatter   - relationship between 2 numeric cols
  histogram - distribution of 1 numeric col
  table     - fallback when no chart fits
"""

import logging
import pandas as pd
import plotly.express as px
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Consistent color palette across all charts
COLORS = [
    "#f59e0b",  # amber   (primary)
    "#3b82f6",  # blue
    "#10b981",  # green
    "#f43f5e",  # rose
    "#a78bfa",  # violet
    "#22d3ee",  # cyan
    "#fb923c",  # orange
    "#34d399",  # emerald
]

# Dark theme layout applied to every chart
BASE_LAYOUT = dict(
    paper_bgcolor="#0c0f1a",
    plot_bgcolor="#0c0f1a",
    font=dict(family="Outfit, sans-serif", color="#e2e8f0", size=12),
    title_font=dict(size=14, color="#f59e0b"),
    legend=dict(
        bgcolor="#0f1220",
        bordercolor="#1a2035",
        borderwidth=1,
        font=dict(color="#8892aa"),
    ),
    margin=dict(l=40, r=40, t=55, b=40),
    xaxis=dict(
        gridcolor="#1a2035",
        zerolinecolor="#1a2035",
        tickfont=dict(color="#8892aa"),
    ),
    yaxis=dict(
        gridcolor="#1a2035",
        zerolinecolor="#1a2035",
        tickfont=dict(color="#8892aa"),
    ),
)


class ChartSelector:

    def select_and_build(
        self, df: pd.DataFrame, question: str
    ) -> Tuple[str, Optional[str]]:
        """
        Main entry point.
        Returns (chart_type, plotly_json_string).
        Returns ("table", None) when no chart is appropriate.
        """
        if df is None or df.empty:
            return "table", None

        # Classify columns
        num_cols  = list(df.select_dtypes(include="number").columns)
        cat_cols  = list(df.select_dtypes(include="object").columns)
        date_cols = self._find_date_cols(df)
        n_rows    = len(df)
        n_cols    = len(df.columns)
        q         = question.lower().strip()

        # Pick chart type
        chart_type = self._decide(q, num_cols, cat_cols, date_cols, n_rows, n_cols)

        # Build the figure
        fig = self._build(df, chart_type, q, num_cols, cat_cols, date_cols)

        if fig is None:
            return "table", None

        return chart_type, fig.to_json()

    # ─────────────────────────────────────────────────────────────────────────
    # DECISION ENGINE
    # ─────────────────────────────────────────────────────────────────────────

    def _decide(self, q, num_cols, cat_cols, date_cols, n_rows, n_cols):
        """
        Rule priority (highest → lowest):
          1. Single aggregate result  → table (nothing to chart)
          2. Question keyword hints   → forced chart type
          3. Date column present      → line chart
          4. Two numeric columns      → scatter
          5. Numeric + few categories → pie
          6. Numeric + categories     → bar
          7. Single numeric column    → histogram
          8. Fallback                 → table
        """

        # ── Rule 1: Single-cell result (one row, one col) ────────────────────
        if n_rows == 1 and n_cols == 1:
            return "table"

        # ── Rule 2: Question keyword overrides ───────────────────────────────

        # LINE — time/trend keywords
        if any(w in q for w in [
            "trend", "over time", "monthly", "daily", "weekly",
            "yearly", "by month", "by year", "by day", "timeline",
            "over months", "over years", "time series",
        ]):
            if (date_cols or cat_cols) and num_cols:
                return "line"

        # PIE — proportion/share keywords
        if any(w in q for w in [
            "proportion", "share", "percentage", "breakdown",
            "composition", "distribution by", "pie",
        ]):
            if num_cols and cat_cols and n_rows <= 12:
                return "pie"

        # HISTOGRAM — distribution keywords
        if any(w in q for w in [
            "distribution", "histogram", "spread", "frequency",
            "how spread", "range of",
        ]):
            if num_cols:
                return "histogram"

        # SCATTER — correlation/relationship keywords
        if any(w in q for w in [
            "correlation", "relationship", "vs", "versus",
            "scatter", "compare two", "against",
        ]):
            if len(num_cols) >= 2:
                return "scatter"

        # BAR — explicit comparison keywords
        if any(w in q for w in [
            "compare", "comparison", "rank", "ranking",
            "top", "bottom", "best", "worst", "bar",
        ]):
            if num_cols and cat_cols:
                return "bar"

        # ── Rule 3: Date column present + numeric → line ─────────────────────
        if date_cols and num_cols:
            return "line"

        # ── Rule 4: Two numeric columns → scatter ────────────────────────────
        if len(num_cols) >= 2 and len(cat_cols) == 0:
            return "scatter"

        # ── Rule 5: Numeric + small category set → pie ───────────────────────
        if num_cols and cat_cols and 2 <= n_rows <= 8:
            return "pie"

        # ── Rule 6: Numeric + categories → bar ───────────────────────────────
        if num_cols and cat_cols:
            return "bar"

        # ── Rule 7: Single numeric column → histogram ─────────────────────────
        if len(num_cols) == 1 and len(cat_cols) == 0:
            return "histogram"

        # ── Rule 8: Fallback ──────────────────────────────────────────────────
        return "table"

    # ─────────────────────────────────────────────────────────────────────────
    # CHART BUILDERS
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self, df, chart_type, q, num_cols, cat_cols, date_cols):
        """Route to the correct builder. Returns Plotly figure or None."""
        try:
            if chart_type == "bar":
                return self._bar(df, q, num_cols, cat_cols)
            if chart_type == "line":
                return self._line(df, q, num_cols, cat_cols, date_cols)
            if chart_type == "pie":
                return self._pie(df, q, num_cols, cat_cols)
            if chart_type == "scatter":
                return self._scatter(df, q, num_cols, cat_cols)
            if chart_type == "histogram":
                return self._histogram(df, q, num_cols)
        except Exception as e:
            logger.warning("Chart build failed (" + chart_type + "): " + str(e))
        return None

    def _bar(self, df, q, num_cols, cat_cols):
        """
        Vertical bar chart.
        X = first categorical column (groups)
        Y = first numeric column (values)
        Color = second categorical column if available (grouped bar)
        Best for: comparing totals/averages across categories.
        """
        x_col = cat_cols[0]
        y_col = num_cols[0]
        color_col = cat_cols[1] if len(cat_cols) > 1 else None
        title = q.capitalize()

        if color_col:
            fig = px.bar(
                df, x=x_col, y=y_col, color=color_col,
                title=title,
                barmode="group",
                color_discrete_sequence=COLORS,
            )
        else:
            fig = px.bar(
                df, x=x_col, y=y_col,
                title=title,
                color_discrete_sequence=COLORS,
                text_auto=".2s",
            )
            fig.update_traces(
                textposition="outside",
                marker_line_color="#0c0f1a",
                marker_line_width=1,
            )

        fig.update_layout(**BASE_LAYOUT)
        return fig

    def _line(self, df, q, num_cols, cat_cols, date_cols):
        """
        Line chart with markers.
        X = date column (preferred) OR first categorical column
        Y = first numeric column
        Color = second categorical column (multiple lines) if available
        Best for: trends over time, sequential data.
        """
        x_col     = date_cols[0] if date_cols else (cat_cols[0] if cat_cols else df.columns[0])
        y_col     = num_cols[0]
        color_col = cat_cols[0] if cat_cols and x_col not in cat_cols else (cat_cols[1] if len(cat_cols) > 1 else None)
        title     = q.capitalize()

        fig = px.line(
            df, x=x_col, y=y_col,
            color=color_col,
            title=title,
            markers=True,
            color_discrete_sequence=COLORS,
        )
        fig.update_traces(
            line=dict(width=2.5),
            marker=dict(size=7, line=dict(width=1.5, color="#0c0f1a")),
        )
        fig.update_layout(**BASE_LAYOUT)
        return fig

    def _pie(self, df, q, num_cols, cat_cols):
        """
        Donut-style pie chart.
        Names = first categorical column
        Values = first numeric column
        Best for: proportions with ≤12 groups.
        If too many slices, groups small ones into 'Other'.
        """
        names_col  = cat_cols[0]
        values_col = num_cols[0]
        title      = q.capitalize()

        # Collapse small slices into 'Other' if >10 categories
        plot_df = df.copy()
        if len(plot_df) > 10:
            plot_df = plot_df.sort_values(values_col, ascending=False)
            top     = plot_df.head(9).copy()
            other   = pd.DataFrame([{
                names_col:  "Other",
                values_col: plot_df.tail(len(plot_df)-9)[values_col].sum(),
            }])
            plot_df = pd.concat([top, other], ignore_index=True)

        fig = px.pie(
            plot_df,
            names=names_col,
            values=values_col,
            title=title,
            hole=0.42,
            color_discrete_sequence=COLORS,
        )
        fig.update_traces(
            textposition="outside",
            textinfo="percent+label",
            pull=[0.03] * len(plot_df),
        )
        fig.update_layout(**BASE_LAYOUT)
        return fig

    def _scatter(self, df, q, num_cols, cat_cols):
        """
        Scatter plot with optional color grouping.
        X = first numeric column
        Y = second numeric column
        Color = first categorical column (if available)
        Size = third numeric column (if available, bubble chart)
        Best for: correlation/relationship between two metrics.
        """
        x_col     = num_cols[0]
        y_col     = num_cols[1]
        color_col = cat_cols[0] if cat_cols else None
        size_col  = num_cols[2] if len(num_cols) > 2 else None
        title     = q.capitalize()

        fig = px.scatter(
            df, x=x_col, y=y_col,
            color=color_col,
            size=size_col,
            title=title,
            color_discrete_sequence=COLORS,
            trendline="ols" if len(df) > 5 and not color_col else None,
        )
        fig.update_traces(
            marker=dict(size=9 if not size_col else None,
                        opacity=0.8,
                        line=dict(width=1, color="#0c0f1a")),
        )
        fig.update_layout(**BASE_LAYOUT)
        return fig

    def _histogram(self, df, q, num_cols):
        """
        Histogram showing value frequency distribution.
        X = first numeric column
        Bins = auto (max 30)
        Best for: understanding how values are spread.
        """
        x_col = num_cols[0]
        title = q.capitalize()

        fig = px.histogram(
            df, x=x_col,
            title=title,
            nbins=min(30, max(10, len(df) // 5)),
            color_discrete_sequence=[COLORS[0]],
        )
        fig.update_traces(
            marker_line_color="#0c0f1a",
            marker_line_width=1,
            opacity=0.85,
        )
        # Add mean line
        try:
            mean_val = df[x_col].mean()
            fig.add_vline(
                x=mean_val,
                line_dash="dash",
                line_color="#10b981",
                annotation_text="mean: " + str(round(mean_val, 2)),
                annotation_font_color="#10b981",
            )
        except Exception:
            pass
        fig.update_layout(**BASE_LAYOUT)
        return fig

    # ─────────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _find_date_cols(self, df: pd.DataFrame):
        """Find columns that look like dates by name or dtype."""
        date_cols = []
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_cols.append(col)
            elif any(kw in col.lower() for kw in ["date","time","month","year","day","created","updated","timestamp"]):
                date_cols.append(col)
        return date_cols
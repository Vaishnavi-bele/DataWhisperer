import pandas as pd
import plotly.express as px
from .intent_detector import IntentDetector


class ChartSelector:

    def __init__(self):
        self.intent_detector = IntentDetector()

    def select_and_build(self, df: pd.DataFrame, question: str):

        # 🚫 EMPTY
        if df is None or df.empty:
            return "table", None

        intent = self.intent_detector.detect(question)

        cols = df.columns.tolist()
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()

        # ─────────────────────────────────────
        # 🎯 INTENT: EMPTY
        # ─────────────────────────────────────
        if intent == "empty":
            return "table", None

        # ─────────────────────────────────────
        # 🎯 INTENT: ONLY NUMERIC
        # ─────────────────────────────────────
        if intent == "only_numeric":
            df = df[num_cols]

        # ─────────────────────────────────────
        # 🎯 INTENT: ONLY CATEGORICAL
        # ─────────────────────────────────────
        if intent == "only_categorical":
            df = df[cat_cols]

        # ─────────────────────────────────────
        # 🎯 INTENT: DISTRIBUTION
        # ─────────────────────────────────────
        if intent == "distribution" and num_cols:
            fig = px.histogram(df, x=num_cols[0], nbins=20,
                               title=f"Distribution of {num_cols[0]}")
            return "histogram", fig.to_json()

        # ─────────────────────────────────────
        # 🎯 SINGLE VALUE → KPI
        # ─────────────────────────────────────
        if len(df) == 1 and len(num_cols) == 1:
            fig = px.bar(df, y=num_cols[0], title=f"{num_cols[0]}")
            return "bar", fig.to_json()

        # ─────────────────────────────────────
        # 📈 TIME SERIES
        # ─────────────────────────────────────
        date_cols = [c for c in cols if "date" in c.lower()]
        if date_cols and num_cols:
            fig = px.line(df, x=date_cols[0], y=num_cols[0], markers=True)
            return "line", fig.to_json()

        # ─────────────────────────────────────
        # 📊 CATEGORY + NUMERIC
        # ─────────────────────────────────────
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            cat = cat_cols[0]
            num = num_cols[0]

            if len(df) <= 5:
                fig = px.pie(df, names=cat, values=num)
                return "pie", fig.to_json()

            fig = px.bar(df, x=cat, y=num)
            return "bar", fig.to_json()

        # ─────────────────────────────────────
        # 📊 ONLY NUMERIC
        # ─────────────────────────────────────
        if len(num_cols) == 1:
            fig = px.histogram(df, x=num_cols[0])
            return "histogram", fig.to_json()

        # ─────────────────────────────────────
        # DEFAULT
        # ─────────────────────────────────────
        return "table", None
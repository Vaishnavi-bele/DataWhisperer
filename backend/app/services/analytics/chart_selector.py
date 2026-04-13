import pandas as pd
import plotly.express as px


class ChartSelector:

    def select_and_build(self, df: pd.DataFrame, question: str):
        # ─────────────────────────────────────
        # 🚫 RULE 0: EMPTY DATA
        # ─────────────────────────────────────
        if df is None or df.empty:
            return "table", None

        cols = df.columns.tolist()
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include="object").columns.tolist()

        q = question.lower()

        # ─────────────────────────────────────
        # 🚫 RULE 1: RAW / LARGE TABLE → NO CHART
        # ─────────────────────────────────────
        if "show all" in q or "list all" in q or len(df) > 100 or len(cols) > 4:
            return "table", None

        # ─────────────────────────────────────
        # 🚫 RULE 2: SINGLE VALUE → NO CHART
        # ─────────────────────────────────────
        if len(df) == 1 and len(num_cols) == 1:
            return "table", None

        # ─────────────────────────────────────
        # 📈 RULE 3: TIME SERIES (HIGH PRIORITY)
        # ─────────────────────────────────────
        date_cols = [c for c in cols if any(x in c.lower() for x in ["date", "time", "month", "year"])]

        if date_cols and num_cols:
            fig = px.line(
                df,
                x=date_cols[0],
                y=num_cols[0],
                title=f"{num_cols[0]} over time",
                markers=True
            )
            return "line", fig.to_json()

        # ─────────────────────────────────────
        # 📊 RULE 4: DISTRIBUTION (QUESTION BASED)
        # ─────────────────────────────────────
        if "distribution" in q or "spread" in q or "histogram" in q:
            if num_cols:
                fig = px.histogram(
                    df,
                    x=num_cols[0],
                    nbins=20,
                    title=f"Distribution of {num_cols[0]}"
                )
                return "histogram", fig.to_json()

        # ─────────────────────────────────────
        # 📊 RULE 5: SINGLE NUMERIC COLUMN
        # ─────────────────────────────────────
        if len(num_cols) == 1 and not cat_cols:
            fig = px.histogram(
                df,
                x=num_cols[0],
                nbins=20,
                title=f"Distribution of {num_cols[0]}"
            )
            return "histogram", fig.to_json()

        # ─────────────────────────────────────
        # 📊 RULE 6: CATEGORY + NUMERIC → BAR / PIE
        # ─────────────────────────────────────
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            cat = cat_cols[0]
            num = num_cols[0]

            # 🔥 TOO MANY CATEGORIES → LIMIT TOP 10
            if len(df) > 10:
                df = df.sort_values(by=num, ascending=False).head(10)

            # PIE only for small groups
            if len(df) <= 5:
                fig = px.pie(
                    df,
                    names=cat,
                    values=num,
                    title=f"{num} by {cat}"
                )
                return "pie", fig.to_json()

            fig = px.bar(
                df,
                x=cat,
                y=num,
                title=f"{num} by {cat}"
            )
            return "bar", fig.to_json()

        # ─────────────────────────────────────
        # 📊 RULE 7: MULTIPLE NUMERIC → SCATTER
        # ─────────────────────────────────────
        if len(num_cols) >= 2:
            fig = px.scatter(
                df,
                x=num_cols[0],
                y=num_cols[1],
                title=f"{num_cols[0]} vs {num_cols[1]}"
            )
            return "scatter", fig.to_json()

        # ─────────────────────────────────────
        # 🧾 DEFAULT → TABLE
        # ─────────────────────────────────────
        return "table", None
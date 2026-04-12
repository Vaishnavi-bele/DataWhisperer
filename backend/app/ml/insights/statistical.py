import numpy as np
import pandas as pd
from typing import Dict, Any

class StatisticalInsightEngine:

    def analyze(self, df: pd.DataFrame, question: str = "") -> Dict[str, Any]:

        if df is None or df.empty:
            return {"error": "No data", "narrative": "No results to analyze."}

        num_cols = df.select_dtypes(include="number").columns.tolist()

        return {
            "summary": self._summary(df, num_cols),
            "trends": self._trends(df, num_cols),
            "correlations": self._correlations(df, num_cols),
            "distribution": self._distribution(df, num_cols),
            "narrative": self._narrative(df, num_cols),
        }

    # ───────── SUMMARY ─────────
    def _summary(self, df, cols):
        out = {}
        for col in cols[:6]:
            s = df[col].dropna()
            if s.empty:
                continue

            out[col] = {
                "mean": round(float(s.mean()), 2),
                "median": round(float(s.median()), 2),
                "std": round(float(s.std()), 2),
                "min": round(float(s.min()), 2),
                "max": round(float(s.max()), 2),
            }
        return out

    # ───────── TRENDS ─────────
    def _trends(self, df, cols):
        results = []

        for col in cols[:4]:
            s = df[col].dropna().reset_index(drop=True)
            if len(s) < 3:
                continue

            x = np.arange(len(s))
            slope = float(np.polyfit(x, s.values, 1)[0])

            if slope > 0:
                direction = "Upward"
            elif slope < 0:
                direction = "Downward"
            else:
                direction = "Flat"

            results.append({
                "column": col,
                "direction": direction,
                "slope": round(slope, 4),
            })

        return results

    # ───────── CORRELATION ─────────
    def _correlations(self, df, cols):
        if len(cols) < 2:
            return []

        try:
            corr = df[cols].corr()
        except:
            return []

        results = []
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                r = corr.iloc[i, j]
                if abs(r) > 0.5:
                    results.append({
                        "col_a": cols[i],
                        "col_b": cols[j],
                        "r": round(float(r), 2),
                    })

        return results

    # ───────── DISTRIBUTION ─────────
    def _distribution(self, df, cols):
        results = []

        for col in cols[:5]:
            s = df[col].dropna()
            if len(s) < 4:
                continue

            skew = float(s.skew())

            if skew > 1:
                shape = "Right-skewed"
            elif skew < -1:
                shape = "Left-skewed"
            else:
                shape = "Normal"

            results.append({
                "column": col,
                "skewness": round(skew, 2),
                "shape": shape,
            })

        return results

    # ───────── NARRATIVE ─────────
    def _narrative(self, df, cols):
        parts = [f"Dataset has {len(df)} rows and {len(df.columns)} columns."]

        if num and len(df) > 1:
            col = num[0]
            parts.append(
                f"'{col}' → avg={df[col].mean():.2f}, "
                f"max={df[col].max():.2f}, "
                f"min={df[col].min():.2f}."
            )

        if cat and num:
            try:
                g = df.groupby(cat[0])[num[0]].sum()
                if not g.empty:
                    top = g.idxmax()
                    parts.append(f"Top {cat[0]}: {top}")
            except:
                pass

        if len(parts) <= 1:
            return "Basic dataset loaded. Ask questions for deeper insights."

        return " ".join(parts)
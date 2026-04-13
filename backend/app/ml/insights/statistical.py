import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class StatisticalInsightEngine:

    def analyze(self, df: pd.DataFrame, question: str = "") -> Dict[str, Any]:
        if df is None or df.empty:
            return {"error": "No data.", "narrative": "No results to analyze."}
        num = df.select_dtypes(include="number").columns.tolist()
        cat = df.select_dtypes(include="object").columns.tolist()
        return {
            "summary":      self._summary(df, num),
            "trends":       self._trends(df, num),
            "correlations": self._correlations(df, num),
            "distribution": self._distribution(df, num),
            "top_bottom":   self._top_bottom(df, num, cat),
            "narrative":    self._narrative(df, num, cat, question),
        }

    def _summary(self, df, num):
        out = {}
        for col in num[:6]:
            s = df[col].dropna()
            if s.empty:
                continue
            out[col] = {
                "count":      int(s.count()),
                "mean":       round(float(s.mean()),   2),
                "median":     round(float(s.median()), 2),
                "std":        round(float(s.std()),    2),
                "min":        round(float(s.min()),    2),
                "max":        round(float(s.max()),    2),
                "range":      round(float(s.max() - s.min()), 2),
                "null_count": int(df[col].isnull().sum()),
            }
        return out

    def _trends(self, df, num):
        results = []
        for col in num[:4]:
            try:
                s = df[col].dropna().reset_index(drop=True)
                if len(s) < 3:
                    continue
                x     = np.arange(len(s))
                slope = float(np.polyfit(x, s.values, 1)[0])
                mean  = s.mean()
                pct   = abs(slope / mean * 100) if mean != 0 else 0
                direction = "Upward" if slope > 0 else "Downward"
                strength  = "strong" if pct > 5 else ("moderate" if pct > 1 else "flat")
                insight   = "'" + col + "' shows a " + strength + " " + direction.lower() + " trend (" + str(round(pct, 1)) + "% change per step)."
                results.append({
                    "column":      col,
                    "direction":   direction,
                    "strength":    strength,
                    "slope":       round(slope, 4),
                    "pct_per_row": round(pct, 2),
                    "insight":     insight,
                })
            except Exception:
                continue
        return results

    def _correlations(self, df, num):
        if len(num) < 2:
            return []
        try:
            corr = df[num].corr()
        except Exception:
            return []
        results = []
        for i in range(len(num)):
            for j in range(i + 1, len(num)):
                r = float(corr.iloc[i, j])
                if abs(r) < 0.3:
                    continue
                direction = "positive" if r > 0 else "negative"
                strength  = "strong" if abs(r) > 0.8 else "moderate"
                insight   = "'" + num[i] + "' and '" + num[j] + "' have a " + strength + " " + direction + " correlation (r=" + str(round(r, 2)) + ")."
                results.append({
                    "col_a":     num[i],
                    "col_b":     num[j],
                    "r":         round(r, 3),
                    "strength":  strength,
                    "direction": direction,
                    "insight":   insight,
                })
        return results

    def _distribution(self, df, num):
        results = []
        for col in num[:5]:
            s = df[col].dropna()
            if len(s) < 4:
                continue
            skew = float(s.skew())
            kurt = float(s.kurt())
            if skew > 1:
                shape = "right-skewed (few very high values)"
            elif skew < -1:
                shape = "left-skewed (few very low values)"
            else:
                shape = "roughly normal"
            use_median = abs(skew) > 1
            if use_median:
                insight = "'" + col + "' is " + shape + ". Use median as center."
            else:
                insight = "'" + col + "' is " + shape + ". Mean is reliable."
            results.append({
                "column":     col,
                "skewness":   round(skew, 3),
                "kurtosis":   round(kurt, 3),
                "shape":      shape,
                "use_median": use_median,
                "insight":    insight,
            })
        return results

    def _top_bottom(self, df, num, cat):
        if not num or not cat:
            return {}
        nc = num[0]
        cc = cat[0]
        try:
            g = df.groupby(cc)[nc].sum().sort_values(ascending=False).round(2)
            top_keys = list(g.head(3).index)
            insight  = "Top '" + cc + "' by '" + nc + "': " + ", ".join(str(k) for k in top_keys) + "."
            return {
                "metric":     nc,
                "grouped_by": cc,
                "top_3":      g.head(3).to_dict(),
                "bottom_3":   g.tail(3).to_dict(),
                "insight":    insight,
            }
        except Exception:
            return {}

    def _narrative(self, df, num, cat, question):
        parts = ["Result has " + str(len(df)) + " rows and " + str(len(df.columns)) + " columns."]
        if num:
            c     = num[0]
            total = df[c].sum()
            avg   = df[c].mean()
            mx    = df[c].max()
            parts.append(
                "For '" + c + "': total=" + str(round(total, 2)) +
                ", avg=" + str(round(avg, 2)) +
                ", max=" + str(round(mx, 2)) + "."
            )
        if cat and num:
            try:
                g   = df.groupby(cat[0])[num[0]].sum()
                top = g.idxmax()
                parts.append("'" + str(top) + "' leads in '" + num[0] + "' with " + str(round(g.max(), 2)) + ".")
            except Exception:
                pass
        elif cat:
            try:
                vc = df[cat[0]].value_counts()
                if not vc.empty:
                    parts.append("Most frequent '" + cat[0] + "': '" + str(vc.index[0]) + "' (" + str(vc.iloc[0]) + " times).")
            except Exception:
                pass
        return " ".join(parts)
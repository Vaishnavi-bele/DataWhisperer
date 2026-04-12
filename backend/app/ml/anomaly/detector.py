import logging
import numpy as np
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AnomalyDetector:

    def detect(
        self,
        df: pd.DataFrame,
        method: str = "isolation_forest",
        contamination: float = 0.05,
        zscore_threshold: float = 3.0
    ) -> Dict[str, Any]:

        num_cols = df.select_dtypes(include="number").columns.tolist()

        # ❌ No numeric columns
        if not num_cols:
            return {
                "error": "No numeric columns found.",
                "total_anomalies": 0
            }

        # 🔥 AUTO FALLBACK (IMPORTANT FIX)
        if len(num_cols) < 2 or len(df) < 30:
            logger.info("Using Z-Score fallback (small dataset)")
            return self._zscore(df, num_cols, zscore_threshold)

        if method == "isolation_forest":
            try:
                return self._iforest(df, num_cols, contamination)
            except Exception as e:
                logger.warning(f"IF failed → fallback to zscore: {e}")
                return self._zscore(df, num_cols, zscore_threshold)

        return self._zscore(df, num_cols, zscore_threshold)

    def _iforest(self, df, num_cols, contamination):
        from sklearn.ensemble import IsolationForest
        from sklearn.preprocessing import StandardScaler

        X = df[num_cols].fillna(df[num_cols].median())
        X_scaled = StandardScaler().fit_transform(X)

        model = IsolationForest(
            contamination=contamination,
            n_estimators=100,
            random_state=42
        )

        preds = model.fit_predict(X_scaled)
        scores = model.decision_function(X_scaled)

        mask = preds == -1
        anom = df[mask].copy()
        anom["anomaly_score"] = np.round(scores[mask], 4)

        return self._result(df, anom, num_cols, "Isolation Forest")

    def _zscore(self, df, num_cols, threshold):
        from scipy import stats

        X = df[num_cols].fillna(df[num_cols].median())
        z = np.abs(stats.zscore(X, nan_policy="omit"))

        mask = (z > threshold).any(axis=1)
        anom = df[mask].copy()
        anom["max_z_score"] = np.round(z[mask].max(axis=1), 4)

        return self._result(df, anom, num_cols, "Z-Score")

    def _result(self, orig, anom, num_cols, method):
        total = len(orig)
        n = len(anom)
        pct = round((n / total) * 100, 2) if total > 0 else 0

        summary = (
            "No anomalies found." if n == 0 else
            f"Found {n} anomalies ({pct}%)."
        )

        return {
            "method": method,
            "total_rows": total,
            "total_anomalies": n,
            "anomaly_percentage": pct,
            "anomalous_rows": anom.head(20).fillna("").to_dict(orient="records"),
            "columns_checked": num_cols,
            "summary": summary,
        }
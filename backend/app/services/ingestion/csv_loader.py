import io, re, chardet
import pandas as pd
from typing import Tuple, Dict, Any

class CSVLoader:
    SEPS = [",", ";", "\t", "|"]

    def load(self, file_bytes: bytes, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        enc = chardet.detect(file_bytes).get("encoding") or "utf-8"
        df = self._parse(file_bytes, enc)

        if df.empty:
            raise ValueError("CSV is empty")

        df = self._clean(df)
        return df, self._meta(df, filename)

    def _parse(self, b, enc):
        for sep in self.SEPS:
            try:
                df = pd.read_csv(io.BytesIO(b), encoding=enc, sep=sep)
                if len(df) > 0:
                    return df
            except:
                continue
        raise ValueError("Failed to parse CSV")

    def _clean(self, df):
        df.columns = [re.sub(r"\W+", "_", str(c).lower()) for c in df.columns]
        return df.dropna(how="all").reset_index(drop=True)

    def _meta(self, df, filename):
        return {
            "filename": filename,
            "rows": len(df),
            "columns": list(df.columns),
            "column_types": {c: str(t) for c, t in df.dtypes.items()},
            "preview": df.head(5).fillna("").to_dict("records"),
            "numeric_columns": list(df.select_dtypes("number").columns),
            "categorical_columns": list(df.select_dtypes("object").columns),
        }
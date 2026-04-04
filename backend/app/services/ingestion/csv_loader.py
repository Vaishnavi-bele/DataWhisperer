import io
import chardet
import pandas as pd
from typing import Tuple, Dict, Any

class CSVLoader:
    SEPARATORS = [",", ";", "\t", "|"]
    MAX_SIZE_MB = 5

    def load(self, file_bytes: bytes, filename: str = "file.csv") -> Tuple[pd.DataFrame, Dict[str, Any]]:
        encoding = self._detect_encoding(file_bytes)
        df = self._parse_csv(file_bytes, encoding, filename)
        df = self._clean(df)
        metadata = self._build_metadata(df, filename)
        return df, metadata

    def _detect_encoding(self, file_bytes: bytes) -> str:
        result = chardet.detect(file_bytes)
        return result.get("encoding") or "utf-8"

    def _parse_csv(self, file_bytes: bytes, encoding: str, filename: str) -> pd.DataFrame:
        last_error = None
        for sep in self.SEPARATORS:
            try:
                df = pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding=encoding,
                    sep=sep,
                    on_bad_lines="skip",
                    low_memory=False,
                )
                if df.shape[0] > 0 and df.shape[1] > 0:
                    return df
            except Exception as e:
                last_error = e
                continue
        raise ValueError(f"Could not parse '{filename}'. Last error: {last_error}")

    def _clean(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [str(c).strip().replace(" ", "_").lower() for c in df.columns]
        str_cols = df.select_dtypes(include="object").columns
        for col in str_cols:
            df[col] = df[col].astype(str).str.strip()
        df = df.infer_objects(copy=False)
        df = df.dropna(how="all").reset_index(drop=True)
        return df

    def _build_metadata(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        return {
            "filename": filename,
            "rows": len(df),
            "columns": list(df.columns),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "preview": df.head(5).to_dict(orient="records"),
            "numeric_columns": list(df.select_dtypes(include="number").columns),
            "categorical_columns": list(df.select_dtypes(include="object").columns),
            "null_counts": df.isnull().sum().to_dict(),
        }

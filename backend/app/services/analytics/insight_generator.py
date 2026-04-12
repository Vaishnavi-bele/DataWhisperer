class InsightGenerator:
    def generate(self, question, df):
        if df.empty:
            return "No results found."

        return f"Returned {len(df)} rows."
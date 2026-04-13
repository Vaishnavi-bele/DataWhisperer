class IntentDetector:

    def detect(self, question: str):
        q = question.lower()

        if "empty" in q:
            return "empty"

        if "only numerical" in q:
            return "only_numeric"

        if "only categorical" in q:
            return "only_categorical"

        if "distribution" in q:
            return "distribution"

        if "trend" in q or "over time" in q:
            return "trend"

        if "top" in q or "best" in q:
            return "ranking"

        return "general"
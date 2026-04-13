"""
DataWhisperer - SQL Generator
PRIMARY:  Flan-T5 (free, local, no API key)
FALLBACK: Rule-based engine covering all question types
"""

import re
import logging
from typing import Tuple, Dict, List, Optional

logger = logging.getLogger(__name__)

PROMPT = """Convert the question to a SQLite SQL query.
Table name: data
Columns: {columns}
Rules:
- Only SELECT queries
- Use ONLY the given column names
- Table name is always 'data'
- Add LIMIT 100 unless the query is an aggregation
Question: {question}
SQL:"""


class SQLGenerator:
    def __init__(self):
        self._pipe = None
        self._rb   = _RuleBasedEngine()

    def generate(self, question: str, schema: Dict[str, str]) -> Tuple[str, str]:
        try:
            sql = self._flan(question, schema)
            if sql and self._is_valid(sql):
                logger.info("Flan-T5 SQL: " + sql[:80])
                return sql, "AI-generated"
        except Exception as e:
            logger.warning("Flan failed: " + str(e))
        sql, expl = self._rb.generate(question, schema)
        logger.info("Rule-based SQL: " + sql[:80])
        return sql, expl

    def _flan(self, question, schema):
        pipe = self._load()
        cols = ", ".join(c + "(" + t[:5] + ")" for c, t in schema.items())
        prompt = PROMPT.format(columns=cols, question=question)
        out = pipe(prompt, max_new_tokens=150, do_sample=False)[0]["generated_text"]
        return self._clean(out)

    def _load(self):
        if self._pipe is None:
            from transformers import pipeline
            logger.info("Loading Flan-T5...")
            self._pipe = pipeline("text2text-generation", model="google/flan-t5-base", max_new_tokens=150)
            logger.info("Flan-T5 ready")
        return self._pipe

    def _clean(self, raw):
        raw = re.sub(r"```(?:sql)?", "", raw, flags=re.IGNORECASE)
        raw = raw.replace("`", "").strip()
        for line in raw.splitlines():
            line = line.strip()
            if line.upper().startswith("SELECT"):
                return line.rstrip(";")
        m = re.search(r"(SELECT\s.+?)(?:;|$)", raw, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else None

    def _is_valid(self, sql):
        blocked = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        u = sql.upper()
        return u.startswith("SELECT") and not any(b in u for b in blocked)


class _RuleBasedEngine:
    """
    Covers all question types:
    basic, count, sum, average, top/bottom, compare,
    group_by, time_series, filter, distribution, min/max
    """

    INTENTS = {
        "show_all":    [r"\bshow all\b", r"\blist all\b", r"\bdisplay all\b", r"\ball data\b", r"\ball entries\b", r"\ball records\b"],
        "count":       [r"\bhow many\b", r"\bcount\b", r"\bnumber of\b", r"\btotal records\b", r"\btotal rows\b"],
        "top_n":       [r"\btop\s+\d+\b", r"\bbest\s+\d+\b"],
        "bottom_n":    [r"\bbottom\s+\d+\b", r"\bworst\s+\d+\b", r"\blowest\s+\d+\b",r"\bleast\b",r"\bsmallest\b"],
        "average":     [r"\baverage\b", r"\bavg\b", r"\bmean\b"],
        "minimum":     [r"\bminimum\b", r"\bmin\b", r"\bsmallest\b", r"\blowest value\b"],
        "maximum":     [r"\bmaximum\b", r"\bmax\b", r"\bhighest\b", r"\blargest\b"],
        "time_series": [r"\btrend\b", r"\bover time\b", r"\bmonthly\b", r"\bdaily\b", r"\bweekly\b", r"\byearly\b", r"\bby month\b", r"\bby year\b", r"\bby day\b"],
        "compare":     [r"\bcompare\b", r"\bvs\b", r"\bversus\b", r"\bperformance\b"],
        "group_sum":   [r"\bby\b", r"\bper\b", r"\beach\b", r"\bgroup\b", r"\bbreakdown\b", r"\bbased on\b", r"\baccording to\b"],
        "sum":         [r"\btotal\b", r"\bsum\b", r"\brevenue\b", r"\bsales\b", r"\bspending\b"],
        "distribution":[r"\bdistribution\b", r"\bhistogram\b", r"\bspread\b"],
        "filter":      [r"\bwhere\b", r"\bfilter\b", r"\bonly\b", r"\bfind\b", r"\bshow\b", r"\blist\b", r"\bis\b",r"\b=\b",r"\bgreater than\b",r">\s*\d+"],
    }

    def generate(self, question: str, schema: Dict[str, str]) -> Tuple[str, str]:
        q         = question.lower().strip()
        num_cols  = [c for c, t in schema.items() if any(x in t for x in ["int","float","double","numeric","decimal"])]
        cat_cols  = [c for c, t in schema.items() if "object" in t or "str" in t]
        date_cols = [c for c in schema if any(x in c.lower() for x in ["date","time","month","year","day","created","updated"])]
        mentioned = self._mentioned(q, list(schema.keys()))
        intent    = self._intent(q)
        sql       = self._build(q, intent, mentioned, num_cols, cat_cols, date_cols, schema)
        return sql, "Rule-based (" + intent + ")"

    def _intent(self, q):
        for intent, patterns in self.INTENTS.items():
            for p in patterns:
                if re.search(p, q):
                    return intent
        # SMART DETECTION
        if "by" in q or "based on" in q:
            return "group_sum"

        return "select_all"

    def _mentioned(self, q, cols):
        found = []
        for col in cols:
            rd = col.replace("_", " ").lower()
            if rd in q:
                found.append(col)
                continue
            words = [w for w in rd.split() if len(w) > 3]
            if words and all(w in q for w in words):
                found.append(col)
                continue
            for w in rd.split():
                if (w + "s" in q or w + "es" in q) and col not in found:
                    found.append(col)
        return found

    def _best_num(self, mentioned, num_cols):
        for c in mentioned:
            if c in num_cols:
                return c
        for p in ["total_revenue","revenue","sales","profit","amount","price","unit_price","total","value","score","quantity","spending","qty", "units", "sold"]:
            for c in num_cols:
                if p in c.lower():
                    return c
        return num_cols[0] if num_cols else None

    def _best_cat(self, mentioned, cat_cols):
        for c in mentioned:
            if c in cat_cols:
                return c
        for p in ["category","region","status","product","name","type","department","segment","city","country","customer"]:
            for c in cat_cols:
                if p in c.lower():
                    return c
        return cat_cols[0] if cat_cols else None

    def _group_col(self, q, cat_cols, date_cols):
        for pat in [r"\bby\s+(\w+)", r"\bper\s+(\w+)", r"\beach\s+(\w+)", r"\bgroup(?:ed)?\s+by\s+(\w+)"]:
            m = re.search(pat, q)
            if m:
                kw = m.group(1).lower()
                for col in cat_cols + date_cols:
                    if kw in col.lower() or col.lower().startswith(kw):
                        return col
        for col in cat_cols + date_cols:
            words = [w for w in col.replace("_"," ").split() if len(w) > 3]
            if any(w in q for w in words):
                return col
        return None

    def _where_clause(self, q, schema):
        conditions = []

        # region detection
        regions = ["north", "south", "east", "west"]
        for r in regions:
            if r in q:
                conditions.append(f"region = '{r.capitalize()}'")

        # product detection
        products = ["laptop", "phone", "tablet"]
        for p in products:
            if p in q:
                conditions.append(f"product = '{p.capitalize()}'")

        # numeric filters
        match = re.search(r'quantity\s*>\s*(\d+)', q)
        if match:
            conditions.append(f"quantity > {match.group(1)}")

        match = re.search(r'quantity\s*<\s*(\d+)', q)
        if match:
            conditions.append(f"quantity < {match.group(1)}")

        return " AND ".join(conditions) if conditions else None

    def _extract_n(self, q, default=10):
        m = re.search(r"\b(\d+)\b", q)
        return min(int(m.group(1)), 500) if m else default

    def _build(self, q, intent, mentioned, num_cols, cat_cols, date_cols, schema):
        nc  = self._best_num(mentioned, num_cols)
        cc  = self._best_cat(mentioned, cat_cols)
        dc  = date_cols[0] if date_cols else None
        flt = self._where_clause(q, schema)
        w   = " WHERE " + flt if flt else ""
        n   = self._extract_n(q)

        # 🔥 KEY FIX → detect "records / rows"
        is_row_query = any(word in q for word in ["record", "records", "row", "rows"])

        # ── SHOW ALL ─────────────────────────────
        if intent == "show_all":
            return "SELECT * FROM data" + w + " LIMIT 100"

        # ── COUNT ───────────────────────────────
        if intent == "count":
            if cc and not is_row_query:
                return f"SELECT {cc}, COUNT(*) as count FROM data{w} GROUP BY {cc} ORDER BY count DESC"
            return f"SELECT COUNT(*) as total_rows FROM data{w}"

        # ── TOP N ───────────────────────────────
        if intent == "top_n":
            if is_row_query:
                if nc:
                    return f"SELECT * FROM data{w} ORDER BY {nc} DESC LIMIT {n}"
                return f"SELECT * FROM data{w} LIMIT {n}"

            if nc and cc:
                return (
                    "SELECT " + cc + ", ROUND(SUM(" + nc + "),2) as total_" + nc +
                    " FROM data" + w +
                    " GROUP BY " + cc +
                    " ORDER BY total_" + nc + " DESC LIMIT " + str(n)
                )

            if nc:
                return f"SELECT * FROM data{w} ORDER BY {nc} DESC LIMIT {n}"

            return f"SELECT * FROM data{w} LIMIT {n}"

        # ── BOTTOM N ────────────────────────────
        if intent == "bottom_n":
            if is_row_query:
                if nc:
                    return f"SELECT * FROM data{w} ORDER BY {nc} ASC LIMIT {n}"
                return f"SELECT * FROM data{w} LIMIT {n}"

            if nc and cc:
                return (
                    "SELECT " + cc + ", ROUND(SUM(" + nc + "),2) as total_" + nc +
                    " FROM data" + w +
                    " GROUP BY " + cc +
                    " ORDER BY total_" + nc + " ASC LIMIT 1"
                )

            if nc:
                return f"SELECT * FROM data{w} ORDER BY {nc} ASC LIMIT {n}"

            return f"SELECT * FROM data{w} LIMIT {n}"

        # ── AVERAGE ─────────────────────────────
        if intent == "average":
            if nc and cc:
                return (
                    f"SELECT {cc}, ROUND(AVG({nc}),2) as avg_{nc} "
                    f"FROM data{w} GROUP BY {cc} ORDER BY avg_{nc} DESC"
                )
            if nc:
                return f"SELECT ROUND(AVG({nc}),2) as avg_{nc} FROM data{w}"
            return f"SELECT * FROM data{w} LIMIT 20"

        # ── SUM ─────────────────────────────────
        if intent == "sum":
            gc = self._group_col(q, cat_cols, date_cols)
            if nc and gc:
                return (
                    f"SELECT {gc}, ROUND(SUM({nc}),2) as total_{nc} "
                    f"FROM data{w} GROUP BY {gc} ORDER BY total_{nc} DESC"
                )
            if nc:
                return f"SELECT ROUND(SUM({nc}),2) as total_{nc} FROM data{w}"
            return f"SELECT * FROM data{w} LIMIT 20"

        # ── GROUP SUM ───────────────────────────
        if intent == "group_sum":
            gc = self._group_col(q, cat_cols, date_cols)
            if nc and gc:
                return (
                    f"SELECT {gc}, ROUND(SUM({nc}),2) as total_{nc}, COUNT(*) as count "
                    f"FROM data{w} GROUP BY {gc} ORDER BY total_{nc} DESC"
                )
            if gc:
                return f"SELECT {gc}, COUNT(*) as count FROM data{w} GROUP BY {gc} ORDER BY count DESC"
            return f"SELECT * FROM data{w} LIMIT 20"

        # ── TIME SERIES ─────────────────────────
        if intent == "time_series":
            if dc and nc:
                return (
                    f"SELECT {dc}, ROUND(SUM({nc}),2) as total_{nc} "
                    f"FROM data{w} GROUP BY {dc} ORDER BY {dc} ASC"
                )
            return f"SELECT * FROM data{w} LIMIT 20"

        # ── COMPARE ─────────────────────────────
        if intent == "compare":
            if cc and nc:
                return (
                    f"SELECT {cc}, ROUND(SUM({nc}),2) as total_{nc}, "
                    f"ROUND(AVG({nc}),2) as avg_{nc}, COUNT(*) as count "
                    f"FROM data{w} GROUP BY {cc} ORDER BY total_{nc} DESC"
                )
            return f"SELECT * FROM data{w} LIMIT 20"

        # ── MIN (FIXED) ───────────────────────────────────────────────
        if intent == "minimum":
            if nc and cc:
                return (
                    "SELECT " + cc + ", ROUND(SUM(" + nc + "),2) as total_" + nc +
                    " FROM data" + w +
                    " GROUP BY " + cc +
                    " ORDER BY total_" + nc + " ASC LIMIT 1"
                )
            if nc:
                return "SELECT MIN(" + nc + ") as min_" + nc + " FROM data" + w

        # ── MAX (FIXED) ───────────────────────────────────────────────
        if intent == "maximum":
            if nc and cc:
                return (
                    "SELECT " + cc + ", ROUND(SUM(" + nc + "),2) as total_" + nc +
                    " FROM data" + w +
                    " GROUP BY " + cc +
                    " ORDER BY total_" + nc + " DESC LIMIT 1"
                )
            if nc:
                return "SELECT MAX(" + nc + ") as max_" + nc + " FROM data" + w

        # ── DISTRIBUTION ───────────────────────
        if intent == "distribution":
            if nc:
                return f"SELECT {nc} FROM data{w} LIMIT 500"
            return f"SELECT * FROM data{w} LIMIT 100"

        # ── FILTER ─────────────────────────────
        if intent == "filter":
            if mentioned:
                return f"SELECT {', '.join(mentioned)} FROM data{w} LIMIT 100"
            return f"SELECT * FROM data{w} LIMIT 100"
        
        
        # SMART: 'which' or 'who' implies single answer
        if ("which" in q or "who" in q or "best" in q or "highest" in q) and nc and cc:
            if "least" in q or "lowest" in q:
                order = "ASC"
            else:
                order = "DESC"

            return (
                "SELECT " + cc + ", ROUND(SUM(" + nc + "),2) as total_" + nc +
                " FROM data" + w +
                " GROUP BY " + cc +
                " ORDER BY total_" + nc + " " + order + " LIMIT 1"
            )
            
        # ── SMART FALLBACK (AUTO GROUP BY) ───────────────────────────
        if nc and cc and intent in ["group_sum", "sum", "compare"]:
            return (
                "SELECT " + cc + ", ROUND(SUM(" + nc + "),2) as total_" + nc +
                " FROM data" + w +
                " GROUP BY " + cc +
                " ORDER BY total_" + nc + " DESC"
            )
            
        # ── DEFAULT ────────────────────────────
        return "SELECT * FROM data LIMIT 20"
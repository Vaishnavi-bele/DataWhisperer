import requests
import pandas as pd
import plotly.io as pio
import plotly.express as px
import streamlit as st

API = "http://localhost:8000/api"

st.set_page_config(
    page_title="DataWhisperer",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════
#  DESIGN SYSTEM
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

:root {
  --bg:      #06080f;
  --card:    #0c0f1a;
  --card2:   #0f1220;
  --border:  #1a2035;
  --border2: #263050;
  --amber:   #f59e0b;
  --ag:      #f59e0b18;
  --ad:      #92600a;
  --blue:    #3b82f6;
  --green:   #10b981;
  --red:     #ef4444;
  --t1:      #f0f4ff;
  --t2:      #8892aa;
  --t3:      #3d4a63;
}

html, body, .stApp { background: var(--bg) !important; color: var(--t1); }
* { font-family: 'Outfit', sans-serif; }
code, pre { font-family: 'JetBrains Mono', monospace !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 0 1.5rem 3rem !important; max-width: 1380px; margin: 0 auto; }
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

.hero {
  padding: 2.5rem 1rem 2rem; text-align: center;
  border-bottom: 1px solid var(--border); margin-bottom: 2rem;
  position: relative; overflow: hidden;
}
.hero::before {
  content: ""; position: absolute; inset: 0;
  background: radial-gradient(ellipse 70% 60% at 50% -5%, #f59e0b14, transparent 65%);
  pointer-events: none;
}
.hero-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: .68rem; letter-spacing: .3em; color: var(--amber);
  text-transform: uppercase; margin-bottom: .6rem; opacity: .8;
}
.hero-title {
  font-size: clamp(2.2rem, 4vw, 3.8rem); font-weight: 800;
  letter-spacing: -.03em; margin: 0 0 .4rem;
  background: linear-gradient(135deg, #fff 25%, #f59e0b 65%, #fbbf24);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  filter: drop-shadow(0 0 28px #f59e0b24);
}
.hero-sub { font-size: .92rem; color: var(--t2); }
.hero-pills {
  display: flex; gap: .45rem; justify-content: center;
  margin-top: .9rem; flex-wrap: wrap;
}
.pill {
  background: var(--card); border: 1px solid var(--border);
  border-radius: 999px; padding: .2rem .7rem;
  font-size: .68rem; color: var(--t2);
  font-family: 'JetBrains Mono', monospace;
}

.slabel {
  font-family: 'JetBrains Mono', monospace;
  font-size: .62rem; letter-spacing: .17em; color: var(--t3);
  text-transform: uppercase; margin-bottom: .7rem;
  display: flex; align-items: center; gap: .5rem;
}
.slabel::after { content: ""; flex: 1; height: 1px; background: var(--border); }

.sgrid { display: grid; grid-template-columns: repeat(3,1fr); gap: .65rem; margin: .7rem 0; }
.scard {
  background: var(--card2); border: 1px solid var(--border);
  border-radius: 9px; padding: .9rem 1rem; position: relative; overflow: hidden;
}
.scard::after {
  content: ""; position: absolute; bottom: 0; left: 0; right: 0;
  height: 2px; background: linear-gradient(90deg, var(--amber), transparent);
}
.snum { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; font-weight: 700; display: block; line-height: 1.1; }
.slbl2 { font-size: .62rem; color: var(--t3); text-transform: uppercase; letter-spacing: .1em; margin-top: .25rem; display: block; }

.ctags { display: flex; flex-wrap: wrap; gap: .28rem; margin: .55rem 0; }
.ctag  { font-family: 'JetBrains Mono', monospace; font-size: .62rem; padding: .18rem .5rem; border-radius: 4px; border: 1px solid var(--border); color: var(--t2); }
.ctag.n { border-color: #f59e0b44; color: var(--amber); background: #f59e0b06; }
.ctag.c { border-color: #3b82f644; color: #60a5fa;      background: #3b82f606; }
.ctag.d { border-color: #10b98144; color: #34d399;      background: #10b98106; }

.stTextInput > div > div > input {
  background: var(--card) !important; border: 1px solid var(--border2) !important;
  border-radius: 9px !important; color: var(--t1) !important;
  font-size: .93rem !important; padding: .75rem 1rem !important; transition: all .2s !important;
}
.stTextInput > div > div > input:focus {
  border-color: var(--amber) !important; box-shadow: 0 0 0 3px var(--ag) !important;
}
.stTextInput > div > div > input::placeholder { color: var(--t3) !important; }

.stButton > button {
  background: var(--card) !important; color: var(--t2) !important;
  border: 1px solid var(--border) !important; border-radius: 7px !important;
  font-size: .73rem !important; padding: .36rem .65rem !important; transition: all .15s !important;
}
.stButton > button:hover { border-color: var(--amber) !important; color: var(--amber) !important; background: var(--ag) !important; }
.stButton > button[kind="primary"] {
  background: linear-gradient(135deg, #d97706, #f59e0b) !important;
  color: #000 !important; border: none !important; font-weight: 700 !important;
  font-size: .9rem !important; border-radius: 9px !important;
  padding: .62rem 1.7rem !important; box-shadow: 0 4px 18px #f59e0b26 !important;
}
.stButton > button[kind="primary"]:hover {
  transform: translateY(-1px) !important; box-shadow: 0 6px 26px #f59e0b38 !important; color: #000 !important;
}

.rcard { background: var(--card); border: 1px solid var(--border); border-radius: 11px; padding: 1.2rem 1.3rem; margin: .9rem 0; }
.rhead { display: flex; align-items: flex-start; gap: .65rem; margin-bottom: .9rem; }
.rnum  {
  font-family: 'JetBrains Mono', monospace; font-size: .58rem; color: var(--amber);
  letter-spacing: .14em; background: var(--ag); border: 1px solid var(--ad);
  border-radius: 4px; padding: .14rem .48rem; white-space: nowrap; margin-top: .2rem;
}
.rq { font-size: 1.05rem; font-weight: 600; color: var(--t1); line-height: 1.3; }

.mbar { display: flex; gap: .45rem; flex-wrap: wrap; margin: .5rem 0 .9rem; }
.ms   { background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: .28rem .7rem; display: flex; align-items: center; gap: .35rem; }
.msv  { font-family: 'JetBrains Mono', monospace; font-size: .78rem; font-weight: 700; color: var(--t1); }
.msl  { font-size: .6rem; color: var(--t3); text-transform: uppercase; letter-spacing: .06em; }
.cbadge { background: var(--ag); border: 1px solid var(--ad); color: var(--amber); font-family: 'JetBrains Mono', monospace; font-size: .58rem; border-radius: 999px; padding: .13rem .55rem; letter-spacing: .07em; }

.sqlb { background: #050710; border: 1px solid var(--border); border-left: 3px solid var(--blue); border-radius: 7px; padding: .8rem 1rem; font-family: 'JetBrains Mono', monospace; font-size: .75rem; color: #7dd3fc; white-space: pre-wrap; word-break: break-word; line-height: 1.62; }
.sqle { font-size: .7rem; color: var(--t3); font-style: italic; margin-bottom: .4rem; font-family: 'JetBrains Mono', monospace; }

.insb { background: #05150e; border: 1px solid #10b98128; border-left: 3px solid var(--green); border-radius: 8px; padding: .85rem 1.05rem; color: #a7f3d0; font-size: .86rem; line-height: 1.68; }
.insh { font-size: .58rem; color: var(--green); font-family: 'JetBrains Mono', monospace; letter-spacing: .17em; text-transform: uppercase; margin-bottom: .35rem; opacity: .8; }
.errb { background: #150505; border: 1px solid #ef444428; border-left: 3px solid var(--red); border-radius: 8px; padding: .8rem 1.05rem; color: #fca5a5; font-size: .83rem; }
.iitem { background: var(--card2); border: 1px solid var(--border); border-radius: 7px; padding: .7rem .9rem; margin: .35rem 0; font-size: .83rem; color: var(--t2); line-height: 1.58; }
.iitem strong { color: var(--t1); }
.ibadge { display: inline-block; font-size: .58rem; font-family: 'JetBrains Mono', monospace; padding: .12rem .45rem; border-radius: 3px; margin-right: .35rem; background: #10b98118; color: var(--green); border: 1px solid #10b98128; }

.astat { display: flex; gap: .8rem; flex-wrap: wrap; margin: .7rem 0; }
.acard { flex: 1; min-width: 90px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: .75rem .9rem; text-align: center; }
.anum  { font-family: 'JetBrains Mono', monospace; font-size: 1.35rem; font-weight: 700; display: block; }
.albl  { font-size: .6rem; color: var(--t3); text-transform: uppercase; letter-spacing: .08em; }
.abox  { padding: 1.1rem; border-radius: 9px; border: 1px solid var(--border); background: var(--card2); margin: .7rem 0; }

[data-testid="stFileUploader"] { border: 1.5px dashed var(--border2) !important; border-radius: 10px !important; background: var(--card) !important; }
[data-testid="stExpander"] { background: var(--card) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
[data-testid="stExpander"] summary { color: var(--t2) !important; font-size: .76rem !important; font-family: 'JetBrains Mono', monospace !important; }
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 8px !important; }
hr { border-color: var(--border) !important; margin: 1rem 0 !important; }
.stSpinner > div { border-top-color: var(--amber) !important; }
.stRadio > div { gap: .45rem; }
.stRadio label { font-size: .8rem !important; color: var(--t2) !important; }
.stTabs [data-baseweb="tab-list"] { background: var(--card) !important; border-radius: 9px !important; padding: .25rem !important; border: 1px solid var(--border) !important; gap: .15rem !important; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: var(--t2) !important; border-radius: 6px !important; font-size: .78rem !important; padding: .38rem .9rem !important; }
.stTabs [aria-selected="true"] { background: var(--ag) !important; color: var(--amber) !important; border: 1px solid var(--ad) !important; }
.dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); margin-right: .4rem; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:.3;} }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
#  SESSION STATE  — initialise once
# ══════════════════════════════════════════════
defaults = {
    "session_id": None,
    "metadata":   None,
    "history":    [],
    "question":   "",
    "anomaly":    None,
    "insights":   None,
    "last_file":  None,      # track filename to avoid re-upload loops
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════
#  API HEALTH
# ══════════════════════════════════════════════
api_ok, api_model = False, "N/A"
try:
    r = requests.get(f"{API}/health", timeout=2)
    if r.status_code == 200:
        h = r.json()
        api_ok    = True
        api_model = h.get("model", "")
except Exception:
    pass

# ══════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════
status_dot = (
    '<span class="dot"></span>API Online &nbsp;·&nbsp; '
    '<span style="font-family:monospace;color:var(--amber);font-size:.67rem">'
    + api_model + "</span>"
    if api_ok
    else '<span style="color:#ef4444">&#9888; Backend offline &mdash; '
         'run: <code>cd backend &amp;&amp; uvicorn app.main:app --reload</code></span>'
)
st.markdown(
    """
    <div class="hero">
      <div class="hero-tag">AI-Powered Data Intelligence</div>
      <h1 class="hero-title">&#128302; DataWhisperer</h1>
      <p class="hero-sub">Upload any CSV &middot; Ask in plain English &middot; Get instant answers</p>
      <div class="hero-pills">
        <span class="pill">NL &#8594; SQL</span>
        <span class="pill">Auto Charts</span>
        <span class="pill">AI Insights</span>
        <span class="pill">Anomaly Detection</span>
        <span class="pill">Statistics</span>
      </div>
      <div style="margin-top:.85rem;font-size:.76rem;color:var(--t3)">"""
    + status_dot
    + "</div></div>",
    unsafe_allow_html=True,
)

# ══════════════════════════════════════════════
#  TWO-COLUMN LAYOUT
# ══════════════════════════════════════════════
left, main = st.columns([1, 2.8], gap="large")

# ─────────────────── LEFT PANEL ───────────────────
with left:
    st.markdown('<div class="slabel">&#128194; Upload Data</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("Drop CSV here", type=["csv"], label_visibility="collapsed")

    # ── Upload logic — only fires when a NEW file is chosen ──────────────────
    if uploaded is not None and uploaded.name != st.session_state.last_file:
        with st.spinner("Reading your data..."):
            try:
                resp = requests.post(
                    f"{API}/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                    timeout=30,
                )
                if resp.status_code == 200:
                    d = resp.json()
                    st.session_state.session_id = d["session_id"]
                    st.session_state.metadata   = d
                    st.session_state.history    = []
                    st.session_state.anomaly    = None
                    st.session_state.insights   = None
                    st.session_state.last_file  = uploaded.name
                    st.success("Loaded " + uploaded.name)
                else:
                    st.error(resp.json().get("detail", "Upload failed"))
            except requests.exceptions.ConnectionError:
                st.error("Backend not running")

    # ── Dataset info panel ───────────────────────────────────────────────────
    if st.session_state.metadata:
        meta    = st.session_state.metadata
        nc_list = meta.get("numeric_columns", [])
        cc_list = meta.get("categorical_columns", [])
        dt_list = [c for c in meta["columns"] if any(x in c.lower() for x in ["date","time","month","year"])]

        st.markdown(
            '<div class="sgrid">'
            '<div class="scard"><span class="snum">' + str(meta["rows"]) + '</span><span class="slbl2">Rows</span></div>'
            '<div class="scard"><span class="snum">' + str(len(meta["columns"])) + '</span><span class="slbl2">Cols</span></div>'
            '<div class="scard"><span class="snum" style="font-size:1rem">' + str(st.session_state.session_id) + '</span><span class="slbl2">Session</span></div>'
            "</div>",
            unsafe_allow_html=True,
        )

        tags_html = ""
        for c in meta["columns"]:
            css = "n" if c in nc_list else ("d" if c in dt_list else "c")
            icon = "#" if css == "n" else ("D" if css == "d" else "A")
            tags_html += '<span class="ctag ' + css + '">' + icon + " " + c + "</span>"
        st.markdown('<div class="ctags">' + tags_html + "</div>", unsafe_allow_html=True)

        with st.expander("Preview (first 5 rows)"):
            st.dataframe(pd.DataFrame(meta["preview"]).fillna(""), use_container_width=True, height=165)

        if st.session_state.history:
            n = len(st.session_state.history)
            st.markdown(
                '<div style="margin-top:.65rem;padding:.55rem .85rem;background:var(--bg);border:1px solid var(--border);border-radius:7px;font-size:.74rem;color:var(--t3)">'
                '<span style="color:var(--amber);font-weight:700">' + str(n) + "</span>"
                + " quer" + ("y" if n == 1 else "ies") + " this session"
                + "</div>",
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            '<div style="text-align:center;padding:2rem 0;color:var(--t3);font-size:.82rem">Upload a CSV file to begin</div>',
            unsafe_allow_html=True,
        )

# ─────────────────── MAIN PANEL ───────────────────
with main:

    if not st.session_state.metadata:
        st.markdown("""
        <div style="text-align:center;padding:5rem 2rem;color:var(--t3)">
          <div style="font-size:3.5rem;margin-bottom:1rem;opacity:.2">&#128302;</div>
          <div style="font-size:1rem;color:var(--t2);font-weight:500;margin-bottom:.4rem">Upload a CSV file to get started</div>
          <div style="font-size:.8rem">Works with any data — sales, logs, surveys, finance, anything</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        meta    = st.session_state.metadata
        nc_list = meta.get("numeric_columns", [])
        cc_list = meta.get("categorical_columns", [])
        nc  = nc_list[0] if nc_list else "value"
        cc  = cc_list[0] if cc_list else "category"
        nc2 = nc_list[1] if len(nc_list) > 1 else nc

        tab1, tab2, tab3 = st.tabs(["&#128172;  Ask Questions", "&#128202;  Data Insights", "&#128302;  Anomaly Detection"])

        # ════════════ TAB 1 — ASK ════════════
        with tab1:
            st.markdown('<div class="slabel">&#9889; Quick starters</div>', unsafe_allow_html=True)

            suggestions = [
                "Show all data",
                "Count rows",
                "Top 5 by " + nc,
                "Total " + nc + " by " + cc,
                "Average " + nc + " per " + cc,
                "Compare " + nc + " by " + cc,
            ]
            sc = st.columns(3)
            for i, sug in enumerate(suggestions):
                with sc[i % 3]:
                    if st.button(sug, key="sug_" + str(i), use_container_width=True):
                        st.session_state.question = sug

            st.write("")
            st.markdown('<div class="slabel">&#128172; Your question</div>', unsafe_allow_html=True)

            question = st.text_input(
                "question",
                value=st.session_state.question,
                placeholder='e.g. "Top 10 by ' + nc + '" or "Count by ' + cc + '"',
                label_visibility="collapsed",
            )

            ask = st.button("&#128302;  Ask DataWhisperer", use_container_width=True, type="primary")

            if ask:
                if not question.strip():
                    st.warning("Please type a question first.")
                elif not st.session_state.session_id:
                    st.error("No data loaded. Upload a CSV first.")
                elif not api_ok:
                    st.error("Backend not running. Start it first.")
                else:
                    with st.spinner("Thinking... (first query loads AI ~20s)"):
                        try:
                            resp = requests.post(
                                f"{API}/query",
                                json={"session_id": st.session_state.session_id, "question": question.strip()},
                                timeout=120,
                            )
                            if resp.status_code == 200:
                                st.session_state.history.insert(0, {"question": question.strip(), "result": resp.json()})
                                st.session_state.question = ""
                                st.rerun()
                            else:
                                st.error(resp.json().get("detail", "Query failed"))
                        except requests.exceptions.ConnectionError:
                            st.error("Backend not running.")
                        except Exception as e:
                            st.error("Error: " + str(e))

            # ── Results ───────────────────────────────────────────────────────
            for idx, entry in enumerate(st.session_state.history):
                q  = entry["question"]
                r  = entry["result"]
                qn = len(st.session_state.history) - idx

                st.markdown(
                    '<div class="rcard">'
                    '<div class="rhead">'
                    '<span class="rnum">Q' + str(qn).zfill(2) + "</span>"
                    '<span class="rq">' + q + "</span>"
                    "</div></div>",
                    unsafe_allow_html=True,
                )

                if not r["success"]:
                    st.markdown('<div class="errb">&#9888; ' + str(r.get("error","Unknown error")) + "</div>", unsafe_allow_html=True)
                    if r.get("sql"):
                        with st.expander("View SQL"):
                            st.markdown('<div class="sqlb">' + r["sql"] + "</div>", unsafe_allow_html=True)
                    st.markdown("<hr>", unsafe_allow_html=True)
                    continue

                cl = (r.get("chart_type") or "table").upper()
                st.markdown(
                    '<div class="mbar">'
                    '<div class="ms"><span class="msv">' + str(r.get("row_count",0)) + '</span><span class="msl">rows</span></div>'
                    '<div class="ms"><span class="msv">' + str(r.get("processing_ms",0)) + 'ms</span><span class="msl">time</span></div>'
                    '<div class="ms"><span class="cbadge">' + cl + " chart</span></div>"
                    "</div>",
                    unsafe_allow_html=True,
                )

                c1, c2 = st.columns([3, 2], gap="medium")

                with c1:
                    if r.get("chart_json") and r.get("chart_type") != "table":
                        try:
                            st.plotly_chart(
                                pio.from_json(r["chart_json"]),
                                use_container_width=True,
                                key="ch_" + str(idx),
                            )
                        except Exception:
                            if r.get("data"):
                                df = pd.DataFrame(r["data"]).fillna("")
                                if df.empty:
                                    st.warning("⚠️ No data found")
                                else:
                                    st.dataframe(df, use_container_width=True, height=240)
                    elif r.get("data"):
                        df = pd.DataFrame(r["data"]).fillna("")

                        if df.empty:
                            st.warning("⚠️ No data found for this query")
                        else:
                            st.dataframe(df, use_container_width=True, height=240)

                with c2:
                    if r.get("insight"):
                        st.markdown(
                            '<div class="insb"><div class="insh">AI Insight</div>' + r["insight"] + "</div>",
                            unsafe_allow_html=True,
                        )
                    st.write("")
                    with st.expander("View generated SQL"):
                        if r.get("sql_explanation"):
                            st.markdown('<div class="sqle">// ' + r["sql_explanation"] + "</div>", unsafe_allow_html=True)
                        st.markdown('<div class="sqlb">' + r.get("sql","") + "</div>", unsafe_allow_html=True)

                if r.get("data") and r.get("chart_type") != "table":
                    with st.expander("Full data table — " + str(r.get("row_count",0)) + " rows"):
                        dff   = pd.DataFrame(r["data"]).fillna("")
                        if dff.empty:
                            st.warning("⚠️ No data to display")
                        else:
                            st.dataframe(dff, use_container_width=True)
                        srch  = st.text_input("Search results", placeholder="Filter...", key="srch_" + str(idx))
                        if srch:
                            dff = dff[dff.astype(str).apply(lambda row: row.str.contains(srch, case=False).any(), axis=1)]
                        st.dataframe(dff, use_container_width=True)
                        st.download_button(
                            "Download CSV", dff.to_csv(index=False),
                            "result_" + str(qn) + ".csv", "text/csv",
                            key="dl_" + str(idx),
                        )

                st.markdown("<hr>", unsafe_allow_html=True)

        # ════════════ TAB 2 — INSIGHTS ════════════
        with tab2:
            st.markdown('<div class="slabel">&#128202; Full Dataset Analysis</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.84rem;color:var(--t2);margin-bottom:1rem">'
                "Automatically analyze your entire dataset — trends, correlations, distribution, and top performers."
                "</div>",
                unsafe_allow_html=True,
            )

            if st.button("&#10024;  Generate Full Insights", use_container_width=True, type="primary"):
                if not st.session_state.session_id:
                    st.error("No data loaded.")
                else:
                    with st.spinner("Analyzing dataset..."):
                        try:
                            resp = requests.post(
                                f"{API}/insights",
                                json={"session_id": st.session_state.session_id, "question": "full analysis"},
                                timeout=60,
                            )
                            if resp.status_code == 200:
                                st.session_state.insights = resp.json()
                            else:
                                st.error("Analysis failed: " + resp.text)
                        except Exception as e:
                            st.error("Error: " + str(e))

            ins = st.session_state.insights
            if ins:
                if ins.get("error"):
                    st.warning(ins["error"])
                else:
                    # Narrative
                    if ins.get("narrative"):
                        st.markdown(
                            '<div class="insb"><div class="insh">Summary</div>' + ins["narrative"] + "</div>",
                            unsafe_allow_html=True,
                        )

                    st.write("")
                    ia, ib = st.columns(2, gap="medium")

                    with ia:
                        # Summary stats
                        if ins.get("summary"):
                            st.markdown('<div class="slabel">Column Statistics</div>', unsafe_allow_html=True)
                            rows = [
                                {"Column": col, "Mean": s["mean"], "Median": s["median"],
                                 "Std": s["std"], "Min": s["min"], "Max": s["max"]}
                                for col, s in ins["summary"].items()
                            ]
                            if rows:
                                st.dataframe(pd.DataFrame(rows).set_index("Column"), use_container_width=True)

                        # Distribution
                        if ins.get("distribution"):
                            st.write("")
                            st.markdown('<div class="slabel">Distribution Shape</div>', unsafe_allow_html=True)
                            for d in ins["distribution"]:
                                icon = "&#128202;" if d["use_median"] else "&#10003;"
                                st.markdown(
                                    '<div class="iitem"><span class="ibadge">' + d["column"] + "</span>"
                                    + icon + " " + d["insight"] + "</div>",
                                    unsafe_allow_html=True,
                                )

                    with ib:
                        # Correlations
                        st.markdown('<div class="slabel">Correlations</div>', unsafe_allow_html=True)
                        if ins.get("correlations"):
                            for corr in ins["correlations"]:
                                arrow = "&#8599;" if corr["direction"] == "positive" else "&#8600;"
                                st.markdown(
                                    '<div class="iitem">' + arrow + " <strong>r=" + str(corr["r"]) + "</strong> &nbsp;&#183;&nbsp; " + corr["insight"] + "</div>",
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.markdown('<div class="iitem">No strong correlations found.</div>', unsafe_allow_html=True)

                        # Trends
                        if ins.get("trends"):
                            st.write("")
                            st.markdown('<div class="slabel">Trends</div>', unsafe_allow_html=True)
                            for t in ins["trends"]:
                                arrow = "&#8593;" if t["direction"] == "Upward" else "&#8595;"
                                st.markdown(
                                    '<div class="iitem">' + arrow + " <strong>" + t["column"] + "</strong>"
                                    + " &nbsp;&#183;&nbsp; " + t["strength"] + " &nbsp;&#183;&nbsp; " + t["insight"] + "</div>",
                                    unsafe_allow_html=True,
                                )

                    # Top/Bottom
                    if ins.get("top_bottom") and ins["top_bottom"].get("top_3"):
                        st.write("")
                        st.markdown('<div class="slabel">Top &amp; Bottom Performers</div>', unsafe_allow_html=True)
                        tb = ins["top_bottom"]
                        ta, tb2 = st.columns(2, gap="medium")
                        with ta:
                            st.markdown("**Top 3**")
                            for name, val in tb["top_3"].items():
                                st.markdown(
                                    '<div class="iitem"><span class="ibadge">' + tb["grouped_by"] + "</span><strong>"
                                    + str(name) + "</strong> — " + str(round(val, 2)) + "</div>",
                                    unsafe_allow_html=True,
                                )
                        with tb2:
                            st.markdown("**Bottom 3**")
                            for name, val in tb["bottom_3"].items():
                                st.markdown(
                                    '<div class="iitem"><span class="ibadge">' + tb["grouped_by"] + "</span>"
                                    + str(name) + " — " + str(round(val, 2)) + "</div>",
                                    unsafe_allow_html=True,
                                )

                    # Column explorer
                    if nc_list:
                        st.write("")
                        st.markdown('<div class="slabel">Explore a Column</div>', unsafe_allow_html=True)
                        col_choice = st.selectbox("Choose column", nc_list, key="insight_col_select")
                        if col_choice:
                            try:
                                resp2 = requests.post(
                                    f"{API}/query",
                                    json={"session_id": st.session_state.session_id, "question": "distribution of " + col_choice},
                                    timeout=60,
                                )
                                if resp2.status_code == 200:
                                    rd = resp2.json()
                                    if rd.get("data") and col_choice in (rd.get("columns") or []):
                                        fdf = pd.DataFrame(rd["data"]).fillna(0)
                                        fig = px.histogram(
                                            fdf, x=col_choice, nbins=20,
                                            title="Distribution of " + col_choice,
                                            color_discrete_sequence=["#f59e0b"],
                                        )
                                        fig.update_layout(
                                            paper_bgcolor="#0c0f1a", plot_bgcolor="#0c0f1a",
                                            font=dict(color="#e2e8f0"),
                                            title_font=dict(color="#f59e0b"),
                                            xaxis=dict(gridcolor="#1a2035"),
                                            yaxis=dict(gridcolor="#1a2035"),
                                            margin=dict(l=30, r=30, t=44, b=28),
                                        )
                                        st.plotly_chart(fig, use_container_width=True)
                            except Exception:
                                pass

        # ════════════ TAB 3 — ANOMALY ════════════
        with tab3:
            st.markdown('<div class="slabel">&#128302; Anomaly Detection</div>', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.84rem;color:var(--t2);margin-bottom:1.1rem">'
                "Finds rows in your data that look unusual or different from the rest. "
                "Great for spotting data errors, outliers, or suspicious records."
                "</div>",
                unsafe_allow_html=True,
            )

            mc, ec = st.columns([1, 2], gap="medium")
            with mc:
                method = st.radio(
                    "Method",
                    ["isolation_forest", "zscore"],
                    key="anom_method",
                    format_func=lambda x: "Smart ML" if x == "isolation_forest" else "Statistical",
                )
            with ec:
                if method == "isolation_forest":
                    st.markdown(
                        '<div class="abox">'
                        '<strong style="color:var(--amber)">Smart ML Method</strong><br>'
                        '<span style="font-size:.8rem;color:var(--t2)">'
                        "Uses machine learning to find rows isolated from the rest. "
                        "Best for catching complex patterns across many columns. "
                        "Expects ~5% of data to be unusual."
                        "</span></div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        '<div class="abox">'
                        '<strong style="color:var(--blue)">Statistical Method</strong><br>'
                        '<span style="font-size:.8rem;color:var(--t2)">'
                        "Flags values more than 3 standard deviations from the average. "
                        "Simple, fast, and easy to explain. "
                        "Best for single-column outliers."
                        "</span></div>",
                        unsafe_allow_html=True,
                    )

            st.write("")
            if st.button("&#128302;  Run Anomaly Detection", use_container_width=True, type="primary"):
                if not st.session_state.session_id:
                    st.error("No data loaded.")
                else:
                    with st.spinner("Scanning for anomalies..."):
                        try:
                            resp = requests.post(
                                f"{API}/anomaly",
                                json={"session_id": st.session_state.session_id, "method": method},
                                timeout=60,
                            )
                            if resp.status_code == 200:
                                st.session_state.anomaly = resp.json()
                            else:
                                st.error("Detection failed: " + resp.text)
                        except Exception as e:
                            st.error("Error: " + str(e))

            anom = st.session_state.anomaly
            if anom:
                if anom.get("error"):
                    st.warning(anom["error"])
                else:
                    n   = anom["total_anomalies"]
                    pct = anom["anomaly_percentage"]
                    tot = anom["total_rows"]

                    nc_clr  = "#ef4444" if n > 0 else "#10b981"
                    pct_clr = "#ef4444" if pct > 10 else "#f59e0b" if pct > 3 else "#10b981"

                    st.markdown(
                        '<div class="astat">'
                        '<div class="acard"><span class="anum">' + str(tot) + '</span><span class="albl">Total Rows</span></div>'
                        '<div class="acard"><span class="anum" style="color:' + nc_clr + '">' + str(n) + '</span><span class="albl">Anomalies</span></div>'
                        '<div class="acard"><span class="anum" style="color:' + pct_clr + '">' + str(pct) + '%</span><span class="albl">Of Data</span></div>'
                        '<div class="acard"><span class="anum" style="font-size:.95rem;color:var(--t2)">' + str(len(anom.get("columns_checked",[]))) + '</span><span class="albl">Cols Checked</span></div>'
                        "</div>",
                        unsafe_allow_html=True,
                    )

                    msg_color = "#ef4444" if n > 0 else "#10b981"
                    msg_bg    = "#150505"  if n > 0 else "#05150e"
                    msg_head  = "Anomalies Found" if n > 0 else "Data Looks Clean"
                    st.markdown(
                        '<div class="insb" style="border-left-color:' + msg_color + ';background:' + msg_bg + '">'
                        '<div class="insh" style="color:' + msg_color + '">' + msg_head + "</div>"
                        + anom["summary"] + "</div>",
                        unsafe_allow_html=True,
                    )

                    if anom.get("anomalous_rows"):
                        st.write("")
                        st.markdown('<div class="slabel">Anomalous Rows (top ' + str(min(20,n)) + ")</div>", unsafe_allow_html=True)
                        adf  = pd.DataFrame(anom["anomalous_rows"]).fillna("")
                        asrch = st.text_input("Filter anomalies", placeholder="Search...", key="anom_search")
                        if asrch:
                            adf = adf[adf.astype(str).apply(lambda row: row.str.contains(asrch, case=False).any(), axis=1)]
                        if adf.empty:
                            st.info("✅ No anomalies found")
                        else:
                            st.dataframe(adf, use_container_width=True, height=270)
                        st.download_button(
                            "Download Anomalies CSV", adf.to_csv(index=False),
                            "anomalies.csv", "text/csv", key="dl_anom",
                        )

                    if anom.get("column_stats"):
                        st.write("")
                        st.markdown('<div class="slabel">Column Statistics Used</div>', unsafe_allow_html=True)
                        cs_rows = [
                            {"Column": c, "Mean": s["mean"], "Std Dev": s["std"], "Min": s["min"], "Max": s["max"]}
                            for c, s in anom["column_stats"].items()
                        ]
                        st.dataframe(pd.DataFrame(cs_rows).set_index("Column"), use_container_width=True)
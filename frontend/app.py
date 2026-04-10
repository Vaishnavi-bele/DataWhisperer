import json
import requests
import pandas as pd
import plotly.io as pio
import streamlit as st

API = "http://localhost:8000/api"
TIMEOUT = 60

st.set_page_config(page_title="DataWhisperer", page_icon="🔮", layout="wide")
import requests
import pandas as pd
import plotly.io as pio
import streamlit as st

API = "http://localhost:8000/api"

st.set_page_config(
    page_title="DataWhisperer",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- CSS ----------------
st.markdown("""
<style>
body, .stApp {background:#06080f;color:#f0f4ff;}
.block-container {max-width:1300px;margin:auto;padding:1rem;}
h1 {text-align:center;color:#f59e0b;}
.card {background:#0c0f1a;border:1px solid #1a2035;padding:1rem;border-radius:10px;margin-bottom:1rem;}
.stat {font-size:1.4rem;font-weight:700;}
.small {font-size:0.8rem;color:#8892aa;}
.sql {background:#050710;padding:10px;border-left:3px solid #3b82f6;border-radius:6px;font-family:monospace;}
.insight {background:#05150e;padding:10px;border-left:3px solid #10b981;border-radius:6px;}
.err {background:#150505;padding:10px;border-left:3px solid #ef4444;border-radius:6px;}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
for k,v in [("session_id",None),("metadata",None),("history",[]),("question","")]:
    if k not in st.session_state:
        st.session_state[k]=v

# ---------------- HEADER ----------------
st.markdown("<h1>🔮 DataWhisperer</h1>", unsafe_allow_html=True)

# ---------------- API CHECK ----------------
api_ok=False
try:
    r=requests.get(f"{API}/health",timeout=2)
    if r.status_code==200:
        api_ok=True
        st.success("✅ API Connected")
except:
    st.error("❌ Backend not running")

# ---------------- LAYOUT ----------------
left, main = st.columns([1,2])

# ---------------- LEFT PANEL ----------------
with left:
    st.markdown("### 📂 Upload CSV")
    uploaded = st.file_uploader("", type=["csv"])

    if uploaded:
        with st.spinner("Uploading..."):
            resp=requests.post(f"{API}/upload",
                files={"file":(uploaded.name,uploaded.getvalue(),"text/csv")})
            if resp.status_code==200:
                data=resp.json()
                st.session_state.session_id=data["session_id"]
                st.session_state.metadata=data
                st.success("Uploaded")

    if st.session_state.metadata:
        meta=st.session_state.metadata
        st.markdown(f"""
        <div class="card">
        <div class="stat">{meta['rows']}</div>
        <div class="small">Rows</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="card">
        <div class="stat">{len(meta['columns'])}</div>
        <div class="small">Columns</div>
        </div>
        """, unsafe_allow_html=True)

        st.write("Columns:", meta["columns"])

# ---------------- MAIN ----------------
with main:
    if st.session_state.metadata:

        st.markdown("### 💬 Ask Question")

        question = st.text_input(
            "",
            value=st.session_state.question,
            placeholder="e.g. top 10 by revenue"
        )

        if st.button("🔮 Ask"):
            resp=requests.post(f"{API}/query",
                json={
                    "session_id":st.session_state.session_id,
                    "question":question
                })
            if resp.status_code==200:
                st.session_state.history.insert(0,{
                    "question":question,
                    "result":resp.json()
                })

        # ---------------- RESULTS ----------------
        for entry in st.session_state.history:
            q=entry["question"]
            r=entry["result"]

            st.markdown(f"### ❓ {q}")

            if not r["success"]:
                st.markdown(f"<div class='err'>{r.get('error')}</div>", unsafe_allow_html=True)
                continue

            col1,col2=st.columns([2,1])

            with col1:
                if r.get("chart_json"):
                    fig=pio.from_json(r["chart_json"])
                    st.plotly_chart(fig,use_container_width=True)
                else:
                    st.dataframe(pd.DataFrame(r["data"]))

            with col2:
                st.markdown(f"""
                <div class="card">
                <div class="stat">{r.get('row_count')}</div>
                <div class="small">Rows</div>
                </div>
                """, unsafe_allow_html=True)

                if r.get("insight"):
                    st.markdown(f"<div class='insight'>{r['insight']}</div>", unsafe_allow_html=True)

            with st.expander("SQL"):
                st.markdown(f"<div class='sql'>{r.get('sql')}</div>", unsafe_allow_html=True)

    else:
        st.write("Upload a CSV to start")
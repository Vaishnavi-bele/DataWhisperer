import json
import requests
import pandas as pd
import plotly.io as pio
import streamlit as st

API = "http://localhost:8000/api"
TIMEOUT = 60

st.set_page_config(page_title="DataWhisperer", page_icon="🔮", layout="wide")


# -----------------------
# API Helper
# -----------------------
def call_api(method, endpoint, **kwargs):
    try:
        url = f"{API}{endpoint}"
        if method == "GET":
            res = requests.get(url, timeout=TIMEOUT, **kwargs)
        else:
            res = requests.post(url, timeout=TIMEOUT, **kwargs)

        if res.status_code == 200:
            return res.json(), None
        return None, res.json().get("detail", res.text)

    except requests.exceptions.ConnectionError:
        return None, "Backend not running."
    except Exception as e:
        return None, str(e)


# -----------------------
# Header
# -----------------------
st.title("🔮 DataWhisperer")
st.caption("Ask anything · get instant intelligence")

# -----------------------
# Sidebar Health Check
# -----------------------
with st.sidebar:
    st.subheader("System Status")

    health, err = call_api("GET", "/health")

    if health:
        st.success("✅ API Online")
        st.caption(f"Model: {health['model']}")
        st.caption(f"Sessions: {health['active_sessions']}")
    else:
        st.error(f"❌ {err}")


# -----------------------
# Session State
# -----------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "metadata" not in st.session_state:
    st.session_state.metadata = None
if "history" not in st.session_state:
    st.session_state.history = []
if "question" not in st.session_state:
    st.session_state.question = ""


# -----------------------
# Upload Section
# -----------------------
st.subheader("📂 Upload CSV")
uploaded = st.file_uploader("Upload file", type=["csv"])

if uploaded:
    if not st.session_state.metadata or st.session_state.metadata["filename"] != uploaded.name:
        with st.spinner("Uploading..."):
            data, err = call_api(
                "POST",
                "/upload",
                files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
            )

            if data:
                st.session_state.session_id = data["session_id"]
                st.session_state.metadata = data
                st.session_state.history = []
                st.success("File uploaded successfully")
            else:
                st.error(err)


# -----------------------
# Dataset Info
# -----------------------
if st.session_state.metadata:
    meta = st.session_state.metadata

    col1, col2, col3 = st.columns(3)
    col1.metric("Rows", f"{meta['rows']:,}")
    col2.metric("Columns", len(meta["columns"]))
    col3.metric("Session", st.session_state.session_id)

    with st.expander("Preview"):
        st.dataframe(pd.DataFrame(meta["preview"]), use_container_width=True)

    # -----------------------
    # Query Section
    # -----------------------
    st.subheader("💬 Ask a Question")

    question = st.text_input(
        "Question",
        value=st.session_state.question,
        placeholder="Show top 10 customers",
    )

    if st.button("Ask", disabled=not st.session_state.session_id):
        if not question.strip():
            st.warning("Enter a question")
        else:
            with st.spinner("Processing..."):
                result, err = call_api(
                    "POST",
                    "/query",
                    json={
                        "session_id": st.session_state.session_id,
                        "question": question.strip(),
                    },
                )

                if result:
                    st.session_state.history.insert(0, {
                        "question": question,
                        "result": result
                    })
                    st.session_state.question = ""
                else:
                    st.error(err)


# -----------------------
# Results Section
# -----------------------
for i, entry in enumerate(st.session_state.history):
    st.divider()

    q = entry["question"]
    r = entry["result"]

    st.markdown(f"### ❓ {q}")

    if not r["success"]:
        st.error(r.get("error", "Error"))
        continue

    # Chart / Table
    if r.get("chart_json") and r.get("chart_type") != "table":
        fig = pio.from_json(r["chart_json"])
        st.plotly_chart(fig, use_container_width=True)
    elif r.get("data"):
        st.dataframe(pd.DataFrame(r["data"]), use_container_width=True)

    # Stats
    col1, col2 = st.columns(2)
    col1.metric("Rows", r.get("row_count", 0))
    col2.metric("Time (ms)", int(r.get("processing_ms", 0)))

    # Insight
    if r.get("insight"):
        st.info(r["insight"])

    # SQL
    with st.expander("SQL"):
        st.code(r.get("sql", ""), language="sql")

else:
    st.info("Upload a CSV to begin 🚀")
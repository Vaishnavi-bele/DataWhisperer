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

# ───────────────────────── SESSION STATE ─────────────────────────
for k, v in [
    ("session_id", None),
    ("metadata", None),
    ("history", []),
    ("question", ""),
]:
    if k not in st.session_state:
        st.session_state[k] = v

# ───────────────────────── API HEALTH ─────────────────────────
api_ok = False
api_name = "N/A"

try:
    r = requests.get(f"{API}/health", timeout=2)
    if r.status_code == 200:
        h = r.json()
        api_ok = True
        api_name = h.get("app_name", "DataWhisperer")
except:
    pass

# ───────────────────────── HEADER ─────────────────────────
st.title("🔮 DataWhisperer")
st.caption("Ask questions → Get SQL → See results instantly")

if api_ok:
    st.success(f"🟢 Backend Connected ({api_name})")
else:
    st.error("🔴 Backend not running → run: uvicorn app.main:app --reload")

# ───────────────────────── LAYOUT ─────────────────────────
left, main = st.columns([1, 2.5])

# ───────────────────────── LEFT PANEL ─────────────────────────
with left:
    st.subheader("📂 Upload CSV")

    uploaded = st.file_uploader("Upload file", type=["csv"])

    if uploaded and (
        st.session_state.metadata is None or
        st.session_state.metadata.get("filename") != uploaded.name
    ):
        with st.spinner("Uploading..."):
            try:
                resp = requests.post(
                    f"{API}/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "text/csv")},
                    timeout=30
                )

                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.session_id = data["session_id"]
                    st.session_state.metadata = data
                    st.session_state.history = []
                    st.success("File uploaded successfully ✅")
                else:
                    try:
                        st.error(resp.json().get("detail", "Upload failed"))
                    except:
                        st.error("Upload failed")

            except:
                st.error("Backend not reachable")

    if st.session_state.metadata:
        meta = st.session_state.metadata

        st.write("### Dataset Info")
        st.write(f"Rows: {meta['rows']}")
        st.write(f"Columns: {len(meta['columns'])}")

        st.write("### Columns")
        st.write(meta["columns"])

        #st.write("### Preview")
        #st.dataframe(pd.DataFrame(meta["preview"]), use_container_width=True)

# ───────────────────────── MAIN PANEL ─────────────────────────
with main:
    if not st.session_state.metadata:
        st.info("Upload a CSV file to start")

    else:
        # ───────── TABS ─────────
        tab1, tab2, tab3 = st.tabs([
            "💬 Ask Questions",
            "📊 Insights",
            "🔬 Anomaly Detection"
        ])

        # ───────── TAB 1 (EXISTING UI) ─────────
        with tab1:
            st.subheader("💬 Ask Questions")

            question = st.text_input(
                "Ask anything about your data",
                value=st.session_state.question,
                placeholder="e.g. Top 5 by revenue"
            )

            if st.button("🔮 Ask", use_container_width=True):
                if not question.strip():
                    st.warning("Enter a question")
                elif not api_ok:
                    st.error("Backend not running")
                else:
                    with st.spinner("Processing your query..."):
                        try:
                            resp = requests.post(
                                f"{API}/query",
                                json={
                                    "session_id": st.session_state.session_id,
                                    "question": question
                                },
                                timeout=60
                            )

                            if resp.status_code == 200:
                                st.session_state.history.insert(0, {
                                    "question": question,
                                    "result": resp.json()
                                })
                                st.session_state.question = ""
                                st.rerun()
                            else:
                                st.error("Query failed")

                        except Exception as e:
                            st.error(f"Error: {e}")

            # RESULTS
            for entry in st.session_state.history:
                q = entry["question"]
                r = entry["result"]

                st.markdown("---")
                st.markdown(f"### ❓ {q}")

                if not r["success"]:
                    st.error(r.get("error", "Error"))
                    continue

                with st.expander("SQL"):
                    st.code(r.get("sql", ""), language="sql")

                if r.get("chart_json"):
                    try:
                        fig = pio.from_json(r["chart_json"])
                        st.plotly_chart(fig, use_container_width=True)
                    except:
                        pass

                if r.get("data"):
                    df = pd.DataFrame(r["data"])
                    st.dataframe(df, use_container_width=True)

                if r.get("insight"):
                    st.success(r["insight"])

        # ───────── TAB 2 (INSIGHTS) ─────────
        with tab2:
            st.subheader("📊 Dataset Insights")

            if st.button("Generate Insights"):
                try:
                    resp = requests.post(
                        f"{API}/insights",
                        json={"session_id": st.session_state.session_id},
                        timeout=60
                    )

                    if resp.status_code == 200:
                        st.json(resp.json())
                    else:
                        st.error("Insights failed")

                except Exception as e:
                    st.error(f"Error: {e}")

        # ───────── TAB 3 (ANOMALY) ─────────
        with tab3:
            st.subheader("🔬 Anomaly Detection")

            if st.button("Run Detection"):
                try:
                    resp = requests.post(
                        f"{API}/anomaly",
                        json={"session_id": st.session_state.session_id},
                        timeout=60
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.anomaly_result = data

                        if data.get("error"):
                            st.warning(data["error"])
                    else:
                        st.error("Detection failed")

                except Exception as e:
                    st.error(f"Error: {e}")
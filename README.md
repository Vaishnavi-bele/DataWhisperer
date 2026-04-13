# 🔮 DataWhisperer — AI-Powered Data Intelligence Platform

> Ask questions about your data in plain English. DataWhisperer translates natural language into SQL, executes queries, generates visualizations, and provides intelligent insights — all in real time.

---

## Key Features

### Data Ingestion

* Upload CSV datasets instantly
* Automatic schema detection (numeric, categorical, datetime)

### Natural Language Querying

* Convert plain English → SQL (AI + rule-based fallback)
* Supports:

  * Top/Bottom queries
  * Aggregations (SUM, AVG, COUNT)
  * Filters & conditions
  * Group-by analysis
  * Time-series queries

### Smart Visualization Engine

* Automatic chart selection based on:
  * Data type
  * Query intent
* Supports:
  * Bar charts
  * Line charts (time-series)
  * Pie charts
  * Histograms
  * Scatter plots
* Handles edge cases (single value, large data, etc.)

### Insight Generation

* Statistical summaries (mean, median, std, range)
* Correlation detection between variables
* Trend analysis (upward/downward patterns)
* Distribution analysis (skewness, kurtosis)
* Top & bottom performers identification
* Auto-generated natural language insights

### Anomaly Detection (ML)

* Isolation Forest (ML-based)
* Z-score (statistical)
* Detects outliers and unusual patterns in data

### Query Safety

* Only SELECT queries allowed
* Blocks unsafe SQL (DROP, DELETE, UPDATE, etc.)

---

## AI/ML Components

* Natural Language → SQL (LLM + rule-based hybrid)
* Statistical analysis engine
* Machine Learning:
  * Isolation Forest (Anomaly Detection)
* Intelligent chart selection (rule + intent-driven)

---

## Tech Stack

| Layer           | Technology                   |
| --------------- | ---------------------------- |
| Backend         | FastAPI                      |
| Frontend        | Streamlit                    |
| Data Processing | Pandas                       |
| Visualization   | Plotly                       |
| Database        | SQLite (in-memory execution) |
| AI/ML           | Flan-T5 (optional), Sklearn  |

---

## Project Structure

```
DataWhisperer/
├── backend/
│   └── app/
│       ├── api/
│       │   └── routes.py
│       │
│       ├── core/
│       │   └── config.py
│       │
│       ├── models/
│       │   └── schemas.py
│       │
│       ├── services/
│       │   ├── ingestion/
│       │   │   └── csv_loader.py
│       │   │
│       │   ├── query_engine/
│       │   │   ├── sql_generator.py
│       │   │   └── sql_validator.py
│       │   │
│       │   ├── analytics/
│       │   │   ├── chart_selector.py
│       │   │   └── insight_generator.py
│       │   │
│       │   └── ml/
│       │       ├── anomaly/
│       │       │   └── detector.py
│       │       └── insights/
│       │           └── statistical.py
│       │
│       ├── utils/
│       │   └── session_store.py
│       │
│       └── main.py
│
├── frontend/
│   └── app.py
│
├── data/
│   └── samples/
│       └── sample.csv
│
├── tests/
│   └── test_phase1.py
│
├── requirements.txt
├── .env
└── .gitignore
```

---

## Example Queries

Try asking:

* "Top 10 products by revenue"
* "Total sales by region"
* "Average profit per category"
* "Revenue over time"
* "Distribution of sales"
* "Only numerical data"
* "Find anomalies in dataset"

---

## How to Run

### Backend
cd backend
uvicorn app.main:app --reload --port 8000

### Frontend
cd frontend
streamlit run app.py

## Safety & Reliability

* SQL injection prevention
* Safe query execution layer
* Graceful handling of empty or invalid queries
* Robust chart fallback logic

---

## 🎯 Future Enhancements

* 🤖 Advanced LLM integration (LangChain, RAG)
* 📊 Auto dashboard generation
* 💬 Conversational memory (multi-turn queries)
* 📁 Support for Excel, JSON, APIs
* ☁️ Deployment (AWS / Docker)
* 📈 Model-based predictions (forecasting)

---

## Resume Highlight

> Built **DataWhisperer**, an AI-powered data intelligence platform that converts natural language queries into SQL, performs real-time analytics, generates interactive visualizations, and detects anomalies using machine learning (Isolation Forest), built with FastAPI, Streamlit, and Python.

---

## Author

**Vaishnavi Bele**

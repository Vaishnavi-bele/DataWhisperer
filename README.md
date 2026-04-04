# 🔮 DataWhisperer — Natural Language Data Intelligence Platform

> Ask questions about your data in plain English. DataWhisperer converts your queries into SQL, executes them, and shows results with charts and insights.

## Features (Phase 1)

* 📂 Upload CSV data
* 💬 Ask questions in natural language
* 🔄 Convert text → SQL (basic)
* 📊 Automatic chart generation
* 🧠 Insight generation (simple analytics)
* 🔐 SQL validation (prevents unsafe queries)

## Tech Stack

| Layer           | Technology                  |
| --------------- | --------------------------- |
| Backend         | FastAPI                     |
| Frontend        | Streamlit                   |
| Data Processing | Pandas                      |
| Charts          | Plotly                      |
| Database        | SQLite                      |
| AI (future)     | LangChain + Open Source LLM |

## Project Structure

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
│       │   └── analytics/
│       │       ├── chart_selector.py
│       │       └── insight_generator.py
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

## 📊 Example Usage

Upload CSV → Ask:

* "Show top 5 customers by revenue"
* "Total sales"
* "Revenue by region"

## 🛡️ Safety

* Only SELECT queries allowed
* Prevents DELETE, DROP, UPDATE

## 🎯 Future Enhancements

* 🤖 LLM-based SQL generation using LangChain
* 📄 PDF and JSON support
* 🔍 Semantic search using embeddings
* 💬 Conversational queries

---

## 📈 Resume Highlight

> Built DataWhisperer, a natural language data analytics platform that converts user queries into SQL, generates visualizations, and provides insights using Python, FastAPI, and Streamlit.

## 👨‍💻 Author

Vaishnavi Bele

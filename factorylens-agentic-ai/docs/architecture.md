# Architecture

```mermaid
flowchart LR
    UI[Streamlit dashboard] --> API[FastAPI]
    API --> V[Transfer-learning vision service]
    V --> C[Defect classifier]
    V --> E[Image embedding]
    E --> F[FAISS similar-case index]
    API --> G[LangGraph agent]
    G --> V
    G --> F
    G --> M[FAISS maintenance-manual index]
    G --> R[Deterministic risk tool]
    G --> H{Human approval}
    H -->|approved| W[Work order]
    H -->|not approved| I[Incident only]
    I --> DB[(SQLite/PostgreSQL)]
    W --> DB
    T[PyTorch training] --> ML[MLflow tracking and registry]
    ML --> V
```

The LLM is optional and may only rewrite the evidence into a concise narrative. Classification, retrieval, risk scoring, approval and database actions remain deterministic and independently testable.

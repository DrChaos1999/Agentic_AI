# API summary

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Runtime, model and index status |
| GET | `/api/v1/model` | Checkpoint and embedding details |
| GET | `/api/v1/index` | FAISS index information |
| POST | `/api/v1/predict` | Classify an uploaded image |
| POST | `/api/v1/search` | Retrieve visually similar indexed cases |
| POST | `/api/v1/analyze` | Run the full LangGraph workflow |
| GET | `/api/v1/incidents` | List stored analyses |
| GET | `/api/v1/work-orders` | List approved work orders |

Open `/docs` after starting FastAPI for interactive Swagger documentation.

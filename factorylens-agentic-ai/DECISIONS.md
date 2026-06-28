# Engineering decisions

1. **Deterministic actions, optional LLM narration.** The LLM cannot change model predictions, risk scores or database actions.
2. **Human gate for work orders.** The agent creates a work order only when `approve_work_order=true` and records the approver.
3. **FAISS exact baseline first.** `IndexFlatIP` provides a measurable reference before HNSW or IVF is introduced.
4. **Class-weighted training.** The dataset is heavily dominated by defect-free images, so macro F1 and weighted loss are required.
5. **Dataset not redistributed.** The original author repository welcomes use but has no standard licence file; the project downloads directly from the source.
6. **Transparent demo mode.** The repository works before training, but every response is explicitly marked `demo-untrained`.

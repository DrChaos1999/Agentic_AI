from app.retrieval.manual_store import ManualFaissStore


def test_manual_store_finds_crack_section(tmp_path):
    manual = tmp_path / "manual.md"
    manual.write_text("# Cracks\nInspect fatigue cracks and alignment.\n# Grinding\nCheck grinding wheel wear.", encoding="utf-8")
    store = ManualFaissStore()
    store.build_from_markdown(manual)
    result = store.search("fatigue crack alignment", top_k=1)
    assert result[0]["heading"] == "Cracks"

from app.agent.risk import calculate_risk


def test_high_risk_crack_with_vibration():
    result = calculate_risk("crack", 0.91, "high", "overheating and unusual vibration", 3)
    assert result.level in {"high", "critical"}
    assert result.score >= 60
    assert result.reasons


def test_free_low_criticality_is_low_risk():
    result = calculate_risk("free", 0.9, "low", "", 0)
    assert result.level == "low"

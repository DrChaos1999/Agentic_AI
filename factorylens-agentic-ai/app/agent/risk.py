from __future__ import annotations

from app.schemas import RiskAssessment

DEFECT_WEIGHTS = {
    "free": 0,
    "uneven": 18,
    "fray": 24,
    "blowhole": 30,
    "crack": 42,
    "break": 48,
}
CRITICALITY_WEIGHTS = {"low": 5, "medium": 15, "high": 28, "critical": 38}
DANGER_KEYWORDS = {
    "overheat": 12,
    "overheating": 12,
    "vibration": 10,
    "noise": 6,
    "smoke": 22,
    "leak": 12,
    "stopped": 18,
    "jam": 15,
    "sparks": 24,
}


def calculate_risk(
    defect_class: str,
    confidence: float,
    criticality: str,
    symptoms: str,
    similar_failures: int = 0,
) -> RiskAssessment:
    reasons: list[str] = []
    score = DEFECT_WEIGHTS.get(defect_class.lower(), 20)
    if score:
        reasons.append(f"Detected defect type '{defect_class}' contributes {score} risk points.")

    criticality_score = CRITICALITY_WEIGHTS.get(criticality.lower(), 15)
    score += criticality_score
    reasons.append(f"Machine criticality '{criticality}' contributes {criticality_score} points.")

    confidence_bonus = int(max(0.0, confidence - 0.5) * 20)
    score += confidence_bonus
    if confidence_bonus:
        reasons.append(f"Model confidence contributes {confidence_bonus} points.")

    lower = symptoms.lower()
    for keyword, weight in DANGER_KEYWORDS.items():
        if keyword in lower:
            score += weight
            reasons.append(f"Symptom keyword '{keyword}' contributes {weight} points.")

    recurrence = min(similar_failures * 3, 12)
    score += recurrence
    if recurrence:
        reasons.append(f"Similar historical failures contribute {recurrence} points.")

    score = max(0, min(100, score))
    if score >= 80:
        level = "critical"
    elif score >= 60:
        level = "high"
    elif score >= 35:
        level = "medium"
    else:
        level = "low"
    return RiskAssessment(level=level, score=score, reasons=reasons or ["No risk signals found."])

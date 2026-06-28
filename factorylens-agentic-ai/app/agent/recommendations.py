from __future__ import annotations

PLAYBOOK: dict[str, dict[str, list[str]]] = {
    "blowhole": {
        "causes": ["trapped gas or porosity", "material contamination", "inconsistent forming pressure"],
        "actions": [
            "isolate the affected batch",
            "inspect upstream material cleanliness",
            "verify forming pressure and temperature records",
            "perform dimensional and integrity checks before release",
        ],
    },
    "break": {
        "causes": ["mechanical overload", "handling impact", "pre-existing crack propagation"],
        "actions": [
            "stop the affected station if breakage can create debris",
            "inspect fixtures and handling path",
            "check loading and clamping force",
            "replace the component and inspect adjacent parts",
        ],
    },
    "crack": {
        "causes": ["fatigue or thermal stress", "excessive clamping", "material brittleness"],
        "actions": [
            "quarantine the component",
            "perform magnified crack inspection",
            "review thermal and load history",
            "inspect alignment and clamping force",
        ],
    },
    "fray": {
        "causes": ["edge abrasion", "worn cutting or grinding tooling", "poor material support"],
        "actions": [
            "inspect tool wear",
            "verify feed speed and support alignment",
            "remove loose fragments",
            "sample neighboring parts from the same batch",
        ],
    },
    "uneven": {
        "causes": ["grinding wheel wear", "misalignment", "unstable feed rate"],
        "actions": [
            "measure surface profile",
            "inspect grinding wheel condition",
            "verify fixture alignment",
            "check feed rate and spindle stability",
        ],
    },
    "free": {
        "causes": ["no visible defect identified"],
        "actions": [
            "continue routine inspection",
            "verify the result if symptoms indicate a hidden failure",
        ],
    },
}


def recommendations_for(defect_class: str, risk_level: str) -> tuple[list[str], list[str]]:
    item = PLAYBOOK.get(defect_class.lower(), PLAYBOOK["free"])
    causes = list(item["causes"])
    actions = list(item["actions"])
    if risk_level in {"high", "critical"}:
        actions.insert(0, "pause operation and request qualified maintenance review")
    if risk_level == "critical":
        actions.insert(1, "apply site lockout/tagout procedure where applicable")
    return causes, actions

from typing import Dict, Any, Tuple, List
import math

def estimate_roi_and_growth(diagnosis_payload: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Lightweight ROI and skill growth simulation.
    Replace with your real financial model later.
    """
    skill_gaps = diagnosis_payload.get("skill_gaps", [])
    if not skill_gaps:
        roi = {"roi_percent": 0, "training_cost_usd": 0, "benefit_usd": 0, "notes": "No skill gaps detected."}
        growth = {"timeline_weeks": [0, 4, 8, 12], "skill_index": [50, 55, 58, 60]}
        return roi, growth

    # Heuristic assumptions
    n_skills = len(skill_gaps)
    training_cost = 5000 + n_skills * 1200  # baseline + per-skill
    avg_gap = sum(max(0, (s.get("target_level_0_100", 60) - s.get("current_level_0_100", 40))) for s in skill_gaps) / n_skills

    # Benefit proportional to average gap and skill count
    benefit = (avg_gap / 100.0) * (30000 + n_skills * 5000)

    roi_percent = 0.0
    if training_cost > 0:
        roi_percent = (benefit - training_cost) / training_cost * 100.0

    roi_payload = {
        "training_cost_usd": round(training_cost, 2),
        "benefit_usd": round(benefit, 2),
        "roi_percent": round(roi_percent, 1),
        "assumptions": [
            "Costs and benefits are simulated using deterministic heuristics.",
            "Replace with your company-specific ROI formula and KPIs."
        ],
    }

    # Growth curve simulation over 12 weeks
    timeline = [0, 2, 4, 8, 12]
    start = 45
    end = min(95, start + avg_gap * 0.7)
    skill_index = []
    for t in timeline:
        # smooth growth curve
        k = 0.35
        value = start + (end - start) * (1 - math.exp(-k * t))
        skill_index.append(round(value, 1))

    growth_payload = {
        "timeline_weeks": timeline,
        "skill_index": skill_index,
        "start_index": start,
        "target_index": round(end, 1)
    }

    return roi_payload, growth_payload

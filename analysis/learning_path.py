from typing import Dict, Any, List
import os
import csv

def build_learning_path_payload(diagnosis_payload: Dict[str, Any]) -> Dict[str, Any]:
    skill_gaps = diagnosis_payload.get("skill_gaps", [])
    # Simple, deterministic design (you can later move this to LLM)
    phases = []

    # Prioritize by priority order
    priority_rank = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    skill_gaps_sorted = sorted(
        skill_gaps,
        key=lambda s: priority_rank.get(s.get("priority", "Medium"), 2)
    )

    # Build phases
    phases.append({
        "phase": "Phase 1 — Foundations",
        "duration_weeks": 4,
        "modality": ["Self-paced", "Workshops"],
        "focus": ["Data literacy", "Core AI concepts", "Governance & ethics"],
    })
    phases.append({
        "phase": "Phase 2 — Applied Capability",
        "duration_weeks": 6,
        "modality": ["Project-based", "Mentoring"],
        "focus": [s.get("skill") for s in skill_gaps_sorted[:6]],
    })
    phases.append({
        "phase": "Phase 3 — Impact & Scale",
        "duration_weeks": 4,
        "modality": ["Coaching", "Capstone"],
        "focus": ["Use-case delivery", "Change management", "KPI/ROI measurement"],
    })

    return {
        "overview": "Corporate learning path aligned with strategy and skill gaps.",
        "phases": phases,
        "governance": {
            "assessment": "Pre/post skill assessment + manager validation",
            "evidence": "Capstone deliverables + portfolio",
            "certification": "Internal badges per phase"
        }
    }

def export_skills_csv(company_id: str, diagnosis_payload: Dict[str, Any], output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "skills_database.csv")

    rows = []
    for s in diagnosis_payload.get("skill_gaps", []):
        rows.append({
            "company_id": company_id,
            "skill": s.get("skill", ""),
            "current_level_0_100": s.get("current_level_0_100", ""),
            "target_level_0_100": s.get("target_level_0_100", ""),
            "priority": s.get("priority", ""),
            "role_impact": s.get("role_impact", ""),
            "estimated_learning_hours": estimate_hours(s.get("priority", "Medium")),
        })

    fieldnames = [
        "company_id", "skill",
        "current_level_0_100", "target_level_0_100",
        "priority", "role_impact",
        "estimated_learning_hours"
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)

    return path

def estimate_hours(priority: str) -> int:
    # deterministic heuristic
    if priority == "Critical":
        return 40
    if priority == "High":
        return 24
    if priority == "Medium":
        return 16
    return 8

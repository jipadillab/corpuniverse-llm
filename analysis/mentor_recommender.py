from typing import Dict, Any, List

def recommend_mentors_payload(diagnosis_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulated mentor/teacher/coach profiles (you can replace with real DB later).
    """
    skill_gaps = diagnosis_payload.get("skill_gaps", [])
    mentors = []

    catalog = [
        {"name": "Senior AI Strategist", "type": "Mentor", "focus": ["AI Strategy", "Governance", "Use-cases"], "score_base": 92},
        {"name": "Data Science Lead", "type": "Teacher", "focus": ["ML Engineering", "Analytics", "MLOps"], "score_base": 90},
        {"name": "Change Management Coach", "type": "Coach", "focus": ["Adoption", "Leadership", "Operating model"], "score_base": 88},
        {"name": "Product Analytics Expert", "type": "Mentor", "focus": ["KPIs", "Experimentation", "Value realization"], "score_base": 87},
    ]

    # Map top skills to best mentor by overlap
    for s in skill_gaps[:6]:
        skill = s.get("skill", "")
        best = None
        best_score = -1
        for c in catalog:
            overlap = sum(1 for f in c["focus"] if f.lower() in skill.lower())
            score = c["score_base"] + overlap * 3
            if score > best_score:
                best_score = score
                best = c

        mentors.append({
            "skill": skill,
            "recommended_persona": best["name"] if best else "Subject Matter Expert",
            "category": best["type"] if best else "Mentor",
            "match_score_0_100": min(99, max(70, best_score if best_score > 0 else 80)),
            "rationale": "Recommended based on skill gap alignment and corporate capability building."
        })

    return {
        "recommended_mentors_by_skill": mentors,
        "delivery_model": {
            "office_hours": "Weekly mentor office hours",
            "coaching": "Bi-weekly leadership coaching for critical roles",
            "teaching": "Modular sessions with assessments"
        }
    }

from typing import Dict, Any

def validate_company_profile(profile: Dict[str, Any]) -> None:
    # Minimal validation; extend as needed
    if not isinstance(profile, dict):
        raise ValueError("Profile must be a JSON object.")

    # Optional fields (do not force strictness)
    allowed = {"industry", "size", "strategy_focus", "region", "company_name"}
    for k in profile.keys():
        if k not in allowed:
            # non-fatal; you may enforce strict schema if desired
            pass

    if "size" in profile and not isinstance(profile["size"], int):
        raise ValueError("size must be an integer if provided.")

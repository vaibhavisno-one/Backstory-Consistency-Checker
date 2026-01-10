def decide_backstory_consistency(evaluated_claims):
    failed_core_claims = [
        c for c in evaluated_claims
        if c["status"] == "FAIL" and c.get("core_trait", False)
    ]

    failed_non_core_claims = [
        c for c in evaluated_claims
        if c["status"] == "FAIL" and not c.get("core_trait", False)
    ]

    if failed_core_claims:
        return {
            "label": 0,
            "rationale": "Core backstory claim contradicted by narrative evidence"
        }

    if len(failed_non_core_claims) >= 2:
        return {
            "label": 0,
            "rationale": "Multiple backstory claims contradicted"
        }

    return {
        "label": 1,
        "rationale": "No decisive contradictions found"
    }

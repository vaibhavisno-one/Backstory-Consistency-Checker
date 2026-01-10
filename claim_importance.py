"""Importance weighting for backstory claims."""

from typing import Dict, Any, List

CLAIM_CATEGORIES = {
    "early_life_event",
    "formative_experience",
    "belief_about_world",
    "fear_or_psychological_constraint",
    "motivation_or_ambition",
    "behavioral_tendency",
    "skill_or_capability",
    "moral_or_narrative_constraint",
}

CATEGORY_BASE_WEIGHTS = {
    "fear_or_psychological_constraint": 0.55,
    "motivation_or_ambition": 0.50,
    "belief_about_world": 0.45,
    "early_life_event": 0.40,
    "formative_experience": 0.35,
    "behavioral_tendency": 0.30,
    "moral_or_narrative_constraint": 0.25,
    "skill_or_capability": 0.20,
}

CORE_TRAIT_BOOST = 0.4


def calculate_importance_weight(claim: Dict[str, Any]) -> float:
    claim_type = claim.get("claim_type", "formative_experience")
    confidence = claim.get("confidence", 0.7)
    core_trait = claim.get("core_trait", False)
    
    base_weight = CATEGORY_BASE_WEIGHTS.get(claim_type, 0.5)
    
    if core_trait:
        weight = base_weight + CORE_TRAIT_BOOST
    else:
        weight = base_weight
    
    confidence_adjustment = (confidence - 0.7) * 0.1
    weight += confidence_adjustment
    
    return max(0.0, min(1.0, weight))


def add_importance_weights(claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    for claim in claims:
        claim["importance_weight"] = calculate_importance_weight(claim)
    return claims


def assign_importance(claims):
    return add_importance_weights(claims)

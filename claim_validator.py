"""Claim schema validation with typed exceptions."""

import re
from typing import List, Dict, Any, Set

ALLOWED_CLAIM_TYPES: Set[str] = {
    "early_life_event",
    "formative_experience",
    "belief_about_world",
    "fear_or_psychological_constraint",
    "motivation_or_ambition",
    "behavioral_tendency",
    "skill_or_capability",
    "moral_or_narrative_constraint",
}


class ClaimValidationError(Exception):
    def __init__(self, message: str, claim_index: int = None, field: str = None):
        self.claim_index = claim_index
        self.field = field
        
        if claim_index is not None:
            if field:
                full_message = f"Claim {claim_index} validation failed on field '{field}': {message}"
            else:
                full_message = f"Claim {claim_index} validation failed: {message}"
        else:
            full_message = message
            
        super().__init__(full_message)


class ClaimValidator:
    REQUIRED_FIELDS: Set[str] = {
        "claim_id",
        "claim_type",
        "claim_text",
        "confidence",
        "core_trait"
    }
    
    def __init__(self):
        self.compound_indicators = [
            r'\band\s+(?:also|then|later)\b',
            r'\bbut\s+(?:also|then|later)\b',
            r'\bwhile\s+(?:also|simultaneously)\b',
            r',\s+and\s+',
            r',\s+but\s+',
            r';\s*\w+',
            r'\.\s+\w+',
        ]
        
        self.strong_compound_patterns = [
            r'\w+\s+and\s+\w+\s+(is|was|are|were|has|have|had|does|did|will|would|can|could)',
            r'(is|was|are|were|has|have|had)\s+\w+.*,\s+and\s+(is|was|are|were|has|have|had)',
        ]

    def _validate_required_fields(self, claim: Dict[str, Any], index: int) -> None:
        if not isinstance(claim, dict):
            raise ClaimValidationError(
                f"Expected dict, got {type(claim).__name__}",
                claim_index=index
            )
        
        missing_fields = self.REQUIRED_FIELDS - set(claim.keys())
        
        if missing_fields:
            raise ClaimValidationError(
                f"Missing required fields: {sorted(missing_fields)}",
                claim_index=index
            )

    def _validate_claim_id(self, claim: Dict[str, Any], index: int) -> None:
        claim_id = claim.get("claim_id")
        
        if not isinstance(claim_id, str):
            raise ClaimValidationError(
                f"claim_id must be str, got {type(claim_id).__name__}",
                claim_index=index,
                field="claim_id"
            )
        
        if not claim_id or not claim_id.strip():
            raise ClaimValidationError(
                "claim_id cannot be empty or whitespace",
                claim_index=index,
                field="claim_id"
            )

    def _validate_claim_type(self, claim: Dict[str, Any], index: int) -> None:
        claim_type = claim.get("claim_type")
        
        if not isinstance(claim_type, str):
            raise ClaimValidationError(
                f"claim_type must be str, got {type(claim_type).__name__}",
                claim_index=index,
                field="claim_type"
            )
        
        if claim_type not in ALLOWED_CLAIM_TYPES:
            raise ClaimValidationError(
                f"claim_type '{claim_type}' not in allowed values: {sorted(ALLOWED_CLAIM_TYPES)}",
                claim_index=index,
                field="claim_type"
            )

    def _validate_claim_text(self, claim: Dict[str, Any], index: int) -> None:
        claim_text = claim.get("claim_text")
        
        if not isinstance(claim_text, str):
            raise ClaimValidationError(
                f"claim_text must be str, got {type(claim_text).__name__}",
                claim_index=index,
                field="claim_text"
            )
        
        if not claim_text or not claim_text.strip():
            raise ClaimValidationError(
                "claim_text cannot be empty or whitespace",
                claim_index=index,
                field="claim_text"
            )
        
        self._check_atomicity(claim_text, index)

    def _check_atomicity(self, text: str, index: int) -> None:
        text_lower = text.lower()
        
        for pattern in self.strong_compound_patterns:
            if re.search(pattern, text_lower):
                raise ClaimValidationError(
                    f"claim_text appears to be compound (contains multiple independent clauses): '{text[:100]}...'",
                    claim_index=index,
                    field="claim_text"
                )
        
        indicator_count = sum(
            1 for pattern in self.compound_indicators 
            if re.search(pattern, text_lower)
        )
        
        if indicator_count >= 2:
            raise ClaimValidationError(
                f"claim_text appears to be compound (multiple conjunctions/separators detected): '{text[:100]}...'",
                claim_index=index,
                field="claim_text"
            )
        
        sentence_endings = len(re.findall(r'[.!?]\s+[A-Z]', text))
        if sentence_endings > 0:
            raise ClaimValidationError(
                f"claim_text contains multiple sentences (not atomic): '{text[:100]}...'",
                claim_index=index,
                field="claim_text"
            )

    def _validate_confidence(self, claim: Dict[str, Any], index: int) -> None:
        confidence = claim.get("confidence")
        
        if not isinstance(confidence, (int, float)):
            raise ClaimValidationError(
                f"confidence must be numeric, got {type(confidence).__name__}",
                claim_index=index,
                field="confidence"
            )
        
        if not (0.0 <= confidence <= 1.0):
            raise ClaimValidationError(
                f"confidence must be in range [0.0, 1.0], got {confidence}",
                claim_index=index,
                field="confidence"
            )

    def _validate_core_trait(self, claim: Dict[str, Any], index: int) -> None:
        core_trait = claim.get("core_trait")
        
        if not isinstance(core_trait, bool):
            raise ClaimValidationError(
                f"core_trait must be bool, got {type(core_trait).__name__}",
                claim_index=index,
                field="core_trait"
            )

    def validate_claim(self, claim: Dict[str, Any], index: int) -> None:
        self._validate_required_fields(claim, index)
        self._validate_claim_id(claim, index)
        self._validate_claim_type(claim, index)
        self._validate_claim_text(claim, index)
        self._validate_confidence(claim, index)
        self._validate_core_trait(claim, index)

    def validate_claims(self, claims: List[Dict[str, Any]]) -> None:
        if not isinstance(claims, list):
            raise ClaimValidationError(
                f"claims must be a list, got {type(claims).__name__}"
            )
        
        if not claims:
            raise ClaimValidationError("claims list cannot be empty")
        
        for index, claim in enumerate(claims):
            self.validate_claim(claim, index)
        
        claim_ids = [claim.get("claim_id") for claim in claims]
        seen_ids = set()
        for index, claim_id in enumerate(claim_ids):
            if claim_id in seen_ids:
                raise ClaimValidationError(
                    f"Duplicate claim_id '{claim_id}' found",
                    claim_index=index,
                    field="claim_id"
                )
            seen_ids.add(claim_id)


def validate_claims(claims: List[Dict[str, Any]]) -> None:
    validator = ClaimValidator()
    validator.validate_claims(claims)

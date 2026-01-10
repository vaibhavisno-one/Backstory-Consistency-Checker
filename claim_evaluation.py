"""Claim evaluation using pattern matching."""

from typing import Dict, Any, List
import re


def _tokenize_for_matching(text: str) -> set:
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    tokens = text.split()
    return set(t for t in tokens if len(t) > 2)


def _detect_negation_patterns(text: str) -> bool:
    negation_patterns = [
        r'\bnot\b', r'\bnever\b', r'\bno\b', r'\bnone\b',
        r'\bneither\b', r'\bnor\b', r'\bwithout\b',
        r'\brefuse[sd]?\b', r'\bdenie[sd]?\b', r'\breject[sed]?\b',
        r'\boppose[sd]?\b', r'\bagainst\b', r'\bcontra\w*\b'
    ]
    
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in negation_patterns)


def _detect_support_patterns(claim_text: str, evidence_text: str) -> bool:
    claim_tokens = _tokenize_for_matching(claim_text)
    evidence_tokens = _tokenize_for_matching(evidence_text)
    
    overlap = claim_tokens & evidence_tokens
    
    if not claim_tokens:
        return False
    
    overlap_ratio = len(overlap) / len(claim_tokens)
    
    if overlap_ratio > 0.25:
        if _detect_negation_patterns(evidence_text):
            evidence_lower = evidence_text.lower()
            for token in overlap:
                token_pos = evidence_lower.find(token)
                if token_pos != -1:
                    context_start = max(0, token_pos - 50)
                    context_end = min(len(evidence_lower), token_pos + 50)
                    context = evidence_lower[context_start:context_end]
                    if _detect_negation_patterns(context):
                        return False
        return True
    
    return False


def _detect_contradiction_patterns(claim_text: str, evidence_text: str) -> bool:
    claim_tokens = _tokenize_for_matching(claim_text)
    evidence_tokens = _tokenize_for_matching(evidence_text)
    
    overlap = claim_tokens & evidence_tokens
    
    if not claim_tokens:
        return False
    
    overlap_ratio = len(overlap) / len(claim_tokens)
    
    if overlap_ratio > 0.2:
        evidence_lower = evidence_text.lower()
        for token in overlap:
            token_pos = evidence_lower.find(token)
            if token_pos != -1:
                context_start = max(0, token_pos - 50)
                context_end = min(len(evidence_lower), token_pos + 50)
                context = evidence_lower[context_start:context_end]
                if _detect_negation_patterns(context):
                    return True
    
    contradiction_keywords = [
        'contrary', 'opposite', 'however', 'but', 'although',
        'despite', 'instead', 'rather', 'unlike', 'whereas'
    ]
    
    evidence_lower = evidence_text.lower()
    for keyword in contradiction_keywords:
        if keyword in evidence_lower and overlap_ratio > 0.15:
            return True
    
    return False


def evaluate_claim(
    claim: Dict[str, Any],
    evidence: List[Dict[str, Any]]
) -> Dict[str, Any]:
    claim_id = claim.get("claim_id", "unknown")
    claim_text = claim.get("claim_text", "")
    
    if not claim_text or not evidence:
        return {
            "claim_id": claim_id,
            "status": "UNKNOWN",
            "supporting_evidence": [],
            "contradicting_evidence": []
        }
    
    supporting_evidence = []
    contradicting_evidence = []
    
    for ev in evidence:
        evidence_text = ev.get("text", "")
        
        if not evidence_text:
            continue
        
        if _detect_contradiction_patterns(claim_text, evidence_text):
            contradicting_evidence.append(ev)
        elif _detect_support_patterns(claim_text, evidence_text):
            supporting_evidence.append(ev)
    
    if contradicting_evidence:
        status = "FAIL"
    elif len(supporting_evidence) >= 2:
        status = "PASS"
    elif len(supporting_evidence) == 1:
        status = "UNKNOWN"
    else:
        status = "UNKNOWN"
    
    return {
        "claim_id": claim_id,
        "status": status,
        "supporting_evidence": supporting_evidence,
        "contradicting_evidence": contradicting_evidence
    }

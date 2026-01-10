"""Temporal evidence grouping into early/mid/late segments."""

from typing import List, Dict, Any

try:
    import pathway as pw
    _PATHWAY_AVAILABLE = hasattr(pw, 'Schema')
except (ImportError, AttributeError):
    _PATHWAY_AVAILABLE = False
    pw = None


def group_evidence_by_timeline(
    evidence: List[Dict[str, Any]]
) -> Dict[str, List[Dict[str, Any]]]:
    if not evidence:
        return {
            "early": [],
            "mid": [],
            "late": []
        }
    
    positions = [e['position'] for e in evidence]
    min_pos = min(positions)
    max_pos = max(positions)
    
    range_size = max_pos - min_pos
    
    if range_size == 0:
        return {
            "early": evidence,
            "mid": [],
            "late": []
        }
    
    segment_size = range_size / 3.0
    early_end = min_pos + segment_size
    mid_end = min_pos + (2 * segment_size)
    
    grouped = {
        "early": [],
        "mid": [],
        "late": []
    }
    
    for e in evidence:
        pos = e['position']
        if pos < early_end:
            grouped["early"].append(e)
        elif pos < mid_end:
            grouped["mid"].append(e)
        else:
            grouped["late"].append(e)
    
    return grouped

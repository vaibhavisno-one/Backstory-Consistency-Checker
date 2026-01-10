"""Pathway claims store (not used in production pipeline)."""

try:
    import pathway as pw
    _PATHWAY_AVAILABLE = hasattr(pw, 'Schema')
except (ImportError, AttributeError):
    _PATHWAY_AVAILABLE = False
    pw = None


if _PATHWAY_AVAILABLE:
    class ClaimSchema(pw.Schema):
        claim_id: str
        claim_type: str
        claim_text: str
        confidence: float
        core_trait: bool
else:
    ClaimSchema = None

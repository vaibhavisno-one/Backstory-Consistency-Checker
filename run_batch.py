import csv
from pathlib import Path
import uuid
from claim_validator import ClaimValidationError
from backstory_decomposer import BackstoryDecomposer
from claim_validator import validate_claims
from claim_importance import add_importance_weights
from novel_ingestion import ingest_novel
from evidence_retrieval import retrieve_evidence_for_claim
from claim_evaluation import evaluate_claim
from backstory_decision import decide_backstory_consistency

INPUT_CSV = Path("test.csv")
OUTPUT_CSV = Path("results.csv")
PROJECT_ROOT = Path(".")


def process_row(book_name: str, backstory: str):
    novel_path = PROJECT_ROOT / f"{book_name}.txt"
    
    if not novel_path.exists():
        raise FileNotFoundError(f"Novel file not found: {novel_path}")
    
    decomposer = BackstoryDecomposer()
    claims = decomposer.decompose(backstory)
    
    try:
        validate_claims(claims)
    except ClaimValidationError:
        repaired_claims = []
        
        for claim in claims:
            text = claim["claim_text"]
            
            if " and " in text or "," in text:
                parts = [p.strip() for p in text.replace(",", " and ").split(" and ") if p.strip()]
                
                for idx, part in enumerate(parts):
                    new_claim = claim.copy()
                    new_claim["claim_text"] = part
                    new_claim["claim_id"] = f"{claim['claim_id']}_split_{idx}_{uuid.uuid4().hex[:6]}"
                    repaired_claims.append(new_claim)
            else:
                repaired_claims.append(claim)
        
        claims = repaired_claims
        validate_claims(claims)
    
    claims = add_importance_weights(claims)
    novel_table = ingest_novel(novel_path)
    
    evaluated_claims = []
    for claim in claims:
        evidence = retrieve_evidence_for_claim(
            novel_table,
            claim["claim_text"],
            top_k=6
        )
        evaluated_claims.append(evaluate_claim(claim, evidence))
    
    return decide_backstory_consistency(evaluated_claims)


def main():
    results = []
    
    with open(INPUT_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            decision = process_row(
                book_name=row["book_name"],
                backstory=row["content"]
            )
            
            results.append({
                "id": row["id"],
                "prediction": decision["label"],
                "rationale": decision["rationale"]
            })
    
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "prediction", "rationale"]
        )
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    main()

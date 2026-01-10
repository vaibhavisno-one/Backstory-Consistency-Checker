"""Evidence retrieval using TF-IDF similarity."""

from typing import List, Dict, Any, Union
from collections import Counter
import re
import math

try:
    import pathway as pw
    _PATHWAY_AVAILABLE = hasattr(pw, 'Schema')
except (ImportError, AttributeError):
    _PATHWAY_AVAILABLE = False
    pw = None


def _tokenize(text: str) -> List[str]:
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    tokens = text.split()
    return [t for t in tokens if t]


def _compute_tf(tokens: List[str]) -> Dict[str, float]:
    if not tokens:
        return {}
    
    token_counts = Counter(tokens)
    total_tokens = len(tokens)
    
    return {token: count / total_tokens for token, count in token_counts.items()}


def _compute_idf(documents: List[List[str]]) -> Dict[str, float]:
    if not documents:
        return {}
    
    num_docs = len(documents)
    doc_freq = Counter()
    
    for doc_tokens in documents:
        unique_tokens = set(doc_tokens)
        for token in unique_tokens:
            doc_freq[token] += 1
    
    idf = {}
    for token, freq in doc_freq.items():
        idf[token] = math.log(num_docs / freq)
    
    return idf


def _compute_tfidf_vector(
    tokens: List[str], 
    idf: Dict[str, float]
) -> Dict[str, float]:
    tf = _compute_tf(tokens)
    tfidf = {}
    
    for token, tf_score in tf.items():
        idf_score = idf.get(token, 0.0)
        tfidf[token] = tf_score * idf_score
    
    return tfidf


def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    if not vec1 or not vec2:
        return 0.0
    
    common_tokens = set(vec1.keys()) & set(vec2.keys())
    dot_product = sum(vec1[token] * vec2[token] for token in common_tokens)
    
    mag1 = math.sqrt(sum(v * v for v in vec1.values()))
    mag2 = math.sqrt(sum(v * v for v in vec2.values()))
    
    if mag1 == 0.0 or mag2 == 0.0:
        return 0.0
    
    return dot_product / (mag1 * mag2)


def retrieve_evidence_for_claim(
    novel_table: Any,
    claim_text: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    from novel_ingestion import export_chunks_to_list
    
    chunks = export_chunks_to_list(novel_table)
    
    if not chunks:
        return []
    
    claim_tokens = _tokenize(claim_text)
    chunk_tokens_list = [_tokenize(chunk['text']) for chunk in chunks]
    
    all_documents = chunk_tokens_list + [claim_tokens]
    idf = _compute_idf(all_documents)
    
    claim_tfidf = _compute_tfidf_vector(claim_tokens, idf)
    
    evidence_list = []
    for i, chunk in enumerate(chunks):
        chunk_tfidf = _compute_tfidf_vector(chunk_tokens_list[i], idf)
        similarity = _cosine_similarity(claim_tfidf, chunk_tfidf)
        
        evidence = {
            "chunk_id": chunk['chunk_id'],
            "text": chunk['text'],
            "position": chunk['position'],
            "relevance_score": similarity
        }
        evidence_list.append(evidence)
    
    evidence_list.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return evidence_list[:top_k]

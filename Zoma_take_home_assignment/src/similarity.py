from __future__ import annotations
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple
from collections import Counter
from .utils import TfidfVectorizerLite, weighted_term_counts, cosine, tokenize, tokenize_tags, vectorize_char_ngrams

@dataclass
class Opportunity:
    id: str
    title: str
    description: str
    tags: List[str]
    industry: str
    country: str
    components: List[str]
    estimated_effort_hours: int

def load_dataset(path: str) -> List[Opportunity]:
    with open(path) as f:
        raw = json.load(f)
    ds: List[Opportunity] = []
    for r in raw:
        ds.append(Opportunity(
            id=r["id"],
            title=r["title"],
            description=r["description"],
            tags=r.get("tags", []),
            industry=r.get("industry", ""),
            country=r.get("country", ""),
            components=r.get("components", []),
            estimated_effort_hours=int(r.get("estimated_effort_hours", 0)),
        ))
    return ds

def load_new_opportunity(path: str) -> Dict[str, Any]:
    with open(path) as f:
        return json.load(f)

def hybrid_similarity(dataset: List[Opportunity], new_opp: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Compute hybrid similarity: 0.7 * TF-IDF cosine + 0.3 * char-3gram cosine, with small metadata boosts.
    Returns list sorted by relevance desc with fields: id, title, score, ref (Opportunity).
    Deterministic with fixed weights and tokenization.
    """
    # Build field-weighted counts for TF-IDF
    docs_counts: List[Counter] = [
        weighted_term_counts(d.title, d.description, d.tags) for d in dataset
    ]
    new_counts = weighted_term_counts(new_opp.get("title", ""), new_opp.get("description", ""), new_opp.get("required_components", []))

    tfidf = TfidfVectorizerLite().fit(docs_counts + [new_counts])
    ds_vecs = tfidf.transform(docs_counts)
    new_vec = tfidf.transform([new_counts])[0]

    # Char 3-gram vectors (using concatenated fields)
    ds_texts = [
        " ".join([d.title, d.description, " ".join(d.tags)]) for d in dataset
    ]
    new_text = " ".join([new_opp.get("title",""), new_opp.get("description",""), " ".join(new_opp.get("required_components", []))])
    _, ds_char_vecs = vectorize_char_ngrams(ds_texts, n=3)
    _, new_char_vecs = vectorize_char_ngrams([new_text], n=3)
    new_char_vec = new_char_vecs[0]

    results: List[Tuple[float, Opportunity]] = []
    for i, d in enumerate(dataset):
        sim_tfidf = cosine(ds_vecs[i], new_vec)  # [0,1] by construction
        sim_char = cosine(ds_char_vecs[i], new_char_vec)
        score = 0.7 * sim_tfidf + 0.3 * sim_char
        # Metadata boosts (deterministic small nudges)
        if d.industry == new_opp.get("industry"):
            score += 0.02
        if d.country == new_opp.get("country"):
            score += 0.02
        results.append((score, d))

    results.sort(key=lambda x: x[0], reverse=True)
    top3 = []
    for score, d in results[:3]:
        # Clamp 0..1
        s = max(0.0, min(1.0, float(score)))
        top3.append({
            "id": d.id,
            "title": d.title,
            "relevance_score": round(s, 4),
            "estimated_effort_hours": d.estimated_effort_hours,
            "ref": d,
        })
    return top3
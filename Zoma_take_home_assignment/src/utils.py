from __future__ import annotations
import re
from typing import List, Dict, Iterable, Tuple
from collections import Counter, defaultdict
import math

_TOKEN_RE = re.compile(r"[a-z0-9]+")

def tokenize(text: str) -> List[str]:
    """Lowercase alnum tokenizer (deterministic, punctuation-insensitive)."""
    if not text:
        return []
    text = text.lower()
    return _TOKEN_RE.findall(text)

def tokenize_tags(tags: Iterable[str]) -> List[str]:
    parts = []
    for t in tags or []:
        parts.extend(tokenize(str(t)))
    return parts

def char_ngrams(text: str, n: int = 3) -> List[str]:
    """Character n-grams (default trigrams) on spaced, lowercased text."""
    if not text:
        return []
    s = re.sub(r"\s+", " ", text.strip().lower())
    if len(s) < n:
        return [s]
    return [s[i:i+n] for i in range(len(s)-n+1)]

class TfidfVectorizerLite:
    """Minimal, deterministic TF-IDF (no external deps).

    - Vocabulary learned from corpus via tokenize()
    - Field weighting supported via passing pre-weighted term counts
    - L2-normalized vectors
    """
    def __init__(self):
        self.idf_: Dict[str, float] = {}
        self.vocab_: Dict[str, int] = {}

    def fit(self, docs: Iterable[Counter]) -> "TfidfVectorizerLite":
        df = Counter()
        docs_list = list(docs)
        for counts in docs_list:
            for term in counts.keys():
                df[term] += 1
        N = len(docs_list)
        # Smooth idf: log((N + 1) / (df + 1)) + 1
        self.idf_ = {t: math.log((N + 1) / (df_t + 1)) + 1.0 for t, df_t in df.items()}
        # vocab in deterministic order
        self.vocab_ = {t: i for i, t in enumerate(sorted(self.idf_.keys()))}
        return self

    def transform(self, docs: Iterable[Counter]) -> List[List[float]]:
        rows: List[List[float]] = []
        for counts in docs:
            vec = [0.0] * len(self.vocab_)
            for term, tf in counts.items():
                j = self.vocab_.get(term)
                if j is None:
                    continue
                vec[j] = float(tf) * self.idf_[term]
            # L2 normalize
            norm = math.sqrt(sum(v*v for v in vec)) or 1.0
            vec = [v / norm for v in vec]
            rows.append(vec)
        return rows

def cosine(a: List[float], b: List[float]) -> float:
    return sum(x*y for x, y in zip(a, b))

def weighted_term_counts(title: str, description: str, tags: Iterable[str],
                         w_title: float = 2.0, w_desc: float = 1.0, w_tags: float = 1.5) -> Counter:
    """Build field-weighted term frequency counts."""
    c = Counter()
    for tok in tokenize(title):
        c[tok] += w_title
    for tok in tokenize(description):
        c[tok] += w_desc
    for tok in tokenize_tags(tags):
        c[tok] += w_tags
    # Convert to integer-like by rounding to 3 decimals for determinism (still float values used)
    return c

def vectorize_char_ngrams(texts: Iterable[str], n: int = 3) -> Tuple[Dict[str, int], List[List[float]]]:
    """Vectorize texts into L2-normalized char n-gram tf-idf-like vectors with IDF=1 (pure TF + normalization).
    Deterministic and simple; returns vocab and vectors.
    """
    grams_list = [Counter(char_ngrams(t, n=n)) for t in texts]
    # Build vocab deterministically
    vocab: Dict[str, int] = {}
    for gram in sorted(set(g for grams in grams_list for g in grams)):
        vocab[gram] = len(vocab)
    vecs: List[List[float]] = []
    for grams in grams_list:
        vec = [0.0] * len(vocab)
        for g, cnt in grams.items():
            j = vocab.get(g)
            if j is not None:
                vec[j] = float(cnt)
        # L2 normalize
        norm = math.sqrt(sum(v*v for v in vec)) or 1.0
        vecs.append([v / norm for v in vec])
    return vocab, vecs
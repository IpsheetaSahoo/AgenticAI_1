# Zoma — AI Engineer Take‑Home (Offline, Deterministic)

## How to Run
```bash
./run.sh
```
This produces `plan.json` in the project root and validates it against `output_schema.json`. It also writes `top3.json` with the top‑3 similar opportunities.

## Approach & Architecture
- **Similarity (Hybrid, deterministic):**
  - Field‑weighted TF‑IDF (title ×2.0, tags ×1.5, description ×1.0) + character 3‑gram cosine.
  - Final score = 0.7 × TF‑IDF + 0.3 × char‑3gram, with small metadata boosts (+0.02 industry, +0.02 country).
  - Implemented from scratch (`TfidfVectorizerLite`) to avoid external deps and guarantee offline reproducibility.
- **Generation (Mock LLM):**
  - A deterministic function converts the top‑3 to a 6–7 phase plan. Weighted average of the top‑3 efforts calibrates total days; then duration is allocated across phases with fixed weights that map to required components (Salesforce, Docxtemplater, S3, similarity, guardrails).
  - Strict IDs (`PH-001`…), integer day caps, DAG‑safe dependencies (sequential chain).
- **Validation & Guardrails:**
  - Primary: `validator.py` (JSON Schema Draft 2020‑12). Code attempts in‑process validation if `jsonschema` is available; otherwise `run.sh` enforces it.
  - If validation fails, a **retry loop** (up to 3 attempts) hardens IDs, clamps durations (1–60), fixes deps, and trims `notes`.
- **CLI & Determinism:**
  - Single command via `run.sh`. No randomness; fixed weights and tokenization.

## Scaling Considerations
- **Latency:** Hybrid scoring over TF‑IDF and char‑grams is O(N·V). For large N, move to incremental IDF updates and sparse vectors (e.g., `scipy.sparse`) or prebuilt embeddings with FAISS/HNSW. Keep char‑grams only for tie‑breaks to cap CPU.
- **Cost & Reliability:** Default path is offline. If enabling an LLM, gate behind a flag and cache prompts; use structured outputs via function‑calling or constrained decoding to prevent retries.
- **Vector Updates:** Maintain per‑field vocabularies with rolling DF counts. Warm‑start IDF; version your vectorizer along with the dataset snapshot.
- **Metadata Filters:** At query time, apply industry/country boosts (as here) or hard filters; use tiebreakers deterministically.

## Next Steps for Production at Zoma
1. Replace mock generation with tool‑augmented LLM using **function‑calling** to emit phases, with schema validation and automatic repair.
2. Add **unit tests** for the retry loop and schema compliance (CI gate).
3. Introduce **hybrid retrieval** with offline MiniLM (e.g., `sentence-transformers` local) plus TF‑IDF to improve semantic recall.
4. Add **observability**: log retrieval scores, decisions, and validation errors; build a small reconciliation view.

## Files
- `src/utils.py` — tokenization and lite TF‑IDF.
- `src/similarity.py` — dataset I/O and hybrid similarity.
- `src/generator.py` — deterministic plan generator + hardening.
- `src/validation.py` — optional in‑process JSON‑Schema validation.
- `main.py` — CLI entrypoint.
- `run.sh` — orchestration + schema validation.
- `plan.json` — generated output (after running).
- `top3.json` — top‑3 similar opportunities.
```
```

## Integration with Zoma's Bottom‑Up / Top‑Down Flows
- **Top‑Down:** Keep the deterministic generator as the "first pass" (zero‑token) and optionally layer a gated LLM chat that refines phase names/descriptions via function‑calling to the schema. The LLM never writes raw JSON directly—only structured outputs—so validation stays deterministic.
- **Bottom‑Up:** Feed historical component/task line items (e.g., Docxtemplater merge fields, Salesforce mappings) to compute bottoms‑up estimates; the similarity step seeds ranges and risks. A reconciliation view compares bottom‑up totals to the top‑down phases and highlights deltas for PM approval.

# Evaluation approach (outline)

Use the Conda environment **`gravitas`** (Python **3.11**): `conda activate gravitas`, then `cd backend && pytest` for automated checks and run the API/UI for manual scenarios below.

1. **Ingestion** — Upload synthetic PDFs (text layer + scanned) and verify `status=ready`, chunk counts, and OCR confidence present on OCR path.
2. **Retrieval** — For a fixed query, inspect `/chunks` and the evidence list returned with the draft: labels `E1…En` should map to real chunk IDs and pages.
3. **Grounding** — Check that `citation_issues` is usually empty after repair; manually verify a sample draft’s `[E#]` tags point to the cited passages.
4. **Edit loop** — Generate draft A, save operator text B, generate draft C with the same query; compare whether the “preferences” block (from B vs A diffs) changes wording in a measurable way (qualitative + optional cosine distance on embeddings of drafts).

Record concrete runs (inputs, queries, outputs) under `samples/` as the project matures.

# Evaluation approach (outline)

Use the Conda environment **`gravitas`** (Python **3.11**): `conda activate gravitas`, then `cd backend && pytest` for automated checks and run the API/UI for manual scenarios below.

1. **Ingestion** — Upload synthetic PDFs (text layer + scanned) and verify `status=ready`, chunk counts, and OCR confidence present on OCR path.
2. **Retrieval** — For a fixed query, inspect `/chunks` and the evidence list returned with the draft: labels `E1…En` should map to real chunk IDs and pages.
3. **Grounding** — Check that `citation_issues` is usually empty after repair; manually verify a sample draft’s `[E#]` tags point to the cited passages.
4. **Edit loop** — Generate draft A, save operator text B, generate draft C with the same query; compare whether the “preferences” block (from B vs A diffs) changes wording in a measurable way (qualitative + optional cosine distance on embeddings of drafts).
5. **Saved drafts** — Run **Generate** twice, confirm two rows in **Saved drafts**, **Open** the older run, and verify text + evidence match what you expect; after **Save operator version**, reopen and confirm the stored text is the operator copy.
6. **Delete** — Delete a document from the list (or document page), confirm the modal, then verify it disappears from `GET /api/documents` and that a new upload can reuse storage without stale Chroma hits for the old id.

Record concrete runs (inputs, queries, outputs) under `samples/` as the project matures.

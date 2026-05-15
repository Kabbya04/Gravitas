# Assumptions and tradeoffs

- **OCR quality** depends on Tesseract and scan quality; when the OCR path runs, an optional **Groq per-page refine** step (`ocr_refine` in `config.yaml`) fixes obvious typos before chunking without inventing facts. Handwriting and very noisy scans may still be partial. The UI surfaces per-chunk OCR confidence when available; chunk `source` may be `ocr_refined` after cleanup.
- **Groq JSON mode** is used to simplify parsing; if the model drifts, the repair pass attempts a fix. Legal correctness is explicitly out of scope for the assessment.
- **BM25 rebuilt per retrieval** keeps code simple and avoids stale indexes when chunks change; for very large corpora you would persist an incremental lexical index.
- **Edit memory** uses coarse line-block diffs and embedding similarity — not a full fine-tuning loop — but provides a concrete, inspectable improvement signal aligned with the rubric.
- **Secrets** never leave the backend; the browser only talks to FastAPI.
- **Document delete** is immediate and irreversible for that id: SQLite cascades remove chunks and drafts; uploaded files and Chroma vectors for the document are removed in the same request. There is no soft-delete or trash bucket in v1.

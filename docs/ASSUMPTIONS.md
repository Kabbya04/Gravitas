# Assumptions and tradeoffs

- **OCR quality** depends on Tesseract and scan quality; handwriting and very noisy scans may be partial. The UI surfaces per-chunk OCR confidence when available.
- **Groq JSON mode** is used to simplify parsing; if the model drifts, the repair pass attempts a fix. Legal correctness is explicitly out of scope for the assessment.
- **BM25 rebuilt per retrieval** keeps code simple and avoids stale indexes when chunks change; for very large corpora you would persist an incremental lexical index.
- **Edit memory** uses coarse line-block diffs and embedding similarity — not a full fine-tuning loop — but provides a concrete, inspectable improvement signal aligned with the rubric.
- **Secrets** never leave the backend; the browser only talks to FastAPI.

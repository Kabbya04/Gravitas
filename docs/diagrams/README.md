# Diagrams (static assets)

These **SVG** files are generated from the Mermaid sources so `docs/ARCHITECTURE.md` renders diagrams in any Markdown preview (including Cursor/VS Code’s built-in preview, which does not evaluate ` ```mermaid ` fences by default).

| File | Generated from |
|------|------------------|
| `architecture.svg` | `architecture.mmd` |
| `rag-pipeline.svg` | `rag-pipeline.mmd` |

## Regenerate after editing `.mmd`

From the repository root (requires Node/npm; first run downloads Puppeteer/Chromium for Mermaid CLI):

```bash
cd docs/diagrams
npx --yes @mermaid-js/mermaid-cli@11.4.0 -i architecture.mmd -o architecture.svg
npx --yes @mermaid-js/mermaid-cli@11.4.0 -i rag-pipeline.mmd -o rag-pipeline.svg
```

Optional: install [Markdown Preview Mermaid Support](https://marketplace.visualstudio.com/items?itemName=bierner.markdown-mermaid) in VS Code/Cursor if you want live Mermaid in fenced code blocks without relying on SVG.

# Raw Sources

Immutable source documents. The LLM reads from here but never modifies these files.

Drop sources here before running an ingest:
- `articles/` — web articles, blog posts (use Obsidian Web Clipper to convert to markdown)
- `papers/` — research papers, whitepapers
- `reports/` — earnings reports, macro reports, broker research
- `assets/` — images referenced in raw documents (downloaded locally)

After dropping a source, tell Claude: "Ingest [filename]" and it will process it into the wiki.


After dropping a source, tell Claude: "Ingest [filename]" — it will update [[index]], [[log]], and all relevant entity/concept pages.

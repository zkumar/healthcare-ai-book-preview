# Healthcare AI — Public Preview

The public preview site for a book in progress on healthcare AI. **This repo is a published subset** — the source of truth is a separate private repository. Only the chapters listed in [`preview-chapters.txt`](preview-chapters.txt) are synced here.

**Live site:** https://zkumar.github.io/healthcare-ai-book-preview/

## How it works

```
PRIVATE repo (healthcare-ai-book)     ← source of truth, all chapters, edited here
   │
   │  sync-preview.sh  (copies only the preview chapters; strips practitioner/ + REVIEW)
   ▼
THIS repo (public)                    ← MkDocs Material site of the preview chapters
   │
   │  mkdocs gh-deploy                 (builds to the gh-pages branch)
   ▼
GitHub Pages                          ← what the public sees
```

## Publishing workflow

1. Edit chapters in the **private** repo as usual.
2. Adjust which chapters are public by editing [`preview-chapters.txt`](preview-chapters.txt).
3. Sync + deploy:

   ```bash
   ./sync-preview.sh --deploy
   ```

   Or sync without deploying (to preview locally first):

   ```bash
   ./sync-preview.sh
   mkdocs serve          # http://127.0.0.1:8000
   ./sync-preview.sh --deploy
   ```

## What is NOT published

- Chapters not listed in `preview-chapters.txt`
- `practitioner/` folders (code, data snapshots)
- `REVIEW.md` editorial-integrity files
- The private repo itself

## Feedback

Reader feedback drives the chapters still being written — open an [issue](https://github.com/zkumar/healthcare-ai-book-preview/issues).

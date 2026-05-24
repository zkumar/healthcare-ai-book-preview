"""Copy selected chapters from the private book repo into the public preview's docs/.

- Reads preview-chapters.txt for the list of chapter slugs.
- For each: copies chapter.md -> docs/<slug>/index.md and figures/ alongside it.
- Strips the '## For Practitioners' section (practitioner/ is private, not published).
- Rewrites the chapter footer to a neutral preview footer.
- Regenerates the `nav:` block in mkdocs.yml from the published chapters.

Run via sync-preview.sh; not meant to be run directly without args.
"""
import re
import shutil
import sys
from pathlib import Path

private = Path(sys.argv[1])
public = Path(sys.argv[2])

chapters_src = private / "chapters"
docs = public / "docs"
config_file = public / "preview-chapters.txt"

slugs = [
    line.strip()
    for line in config_file.read_text().splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]

# Wipe previously-synced chapter dirs (keep index.md, assets, stylesheets)
for d in docs.iterdir():
    if d.is_dir() and re.match(r"^\d{2}-", d.name):
        shutil.rmtree(d)

nav_entries = []
for slug in slugs:
    src_dir = chapters_src / slug
    src_md = src_dir / "chapter.md"
    if not src_md.exists():
        print(f"  WARNING: {slug}/chapter.md not found — skipping")
        continue

    dest_dir = docs / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    md = src_md.read_text()

    # Strip the "## For Practitioners" section up to the next horizontal rule.
    md = re.sub(
        r"\n## For Practitioners\b.*?(?=\n---\n)",
        "",
        md,
        flags=re.DOTALL,
    )

    # Replace the private footer with a neutral preview footer.
    md = re.sub(
        r"\*Chapter (\d+) of 21 ·[^\n]*\*",
        lambda m: (
            f"*Chapter {m.group(1)} · Preview edition. "
            "The complete book is in progress — "
            "[share feedback](https://github.com/zkumar/healthcare-ai-book-preview/issues).*"
        ),
        md,
    )

    (dest_dir / "index.md").write_text(md)

    # Copy figures alongside so relative figures/ paths resolve.
    src_figs = src_dir / "figures"
    if src_figs.is_dir():
        shutil.copytree(src_figs, dest_dir / "figures", dirs_exist_ok=True)

    # Derive a human title from the H1 in the markdown.
    h1 = re.search(r"^#\s+(.+)$", md, flags=re.MULTILINE)
    title = h1.group(1).strip() if h1 else slug
    nav_entries.append((title, f"{slug}/index.md"))
    n_figs = len(list((dest_dir / "figures").glob("*"))) if (dest_dir / "figures").is_dir() else 0
    print(f"  {slug}: synced ({n_figs} figures)")

# Regenerate the nav block in mkdocs.yml between the NAV markers.
mkdocs_yml = public / "mkdocs.yml"
text = mkdocs_yml.read_text()
nav_lines = ["nav:", "  - Home: index.md"]
for title, path in nav_entries:
    # Quote titles that contain a colon (YAML safety).
    safe_title = f'"{title}"' if ":" in title else title
    nav_lines.append(f"  - {safe_title}: {path}")
nav_block = "\n".join(nav_lines)

text = re.sub(
    r"# NAV-START.*?# NAV-END",
    f"# NAV-START\n{nav_block}\n# NAV-END",
    text,
    flags=re.DOTALL,
)
mkdocs_yml.write_text(text)
print(f"\nNav rebuilt with {len(nav_entries)} chapter(s).")

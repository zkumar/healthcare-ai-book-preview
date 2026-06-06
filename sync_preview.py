"""Copy selected chapters from the private book repo into the public preview's docs/.

For each chapter in preview-chapters.txt:
  - chapter.md          -> docs/<slug>/index.md  (prose; "For Practitioners" pointer rewritten)
  - figures/            -> docs/<slug>/figures/
  - practitioner/       -> docs/<slug>/practitioner.md  (data snapshots + rendered code)
      practitioner/code/*.py  -> docs/<slug>/code/*.py  and  *.ipynb (via jupytext, for Colab)
      Colab badges rewritten from the PRIVATE repo to THIS PUBLIC repo.

Regenerates the `nav:` block in mkdocs.yml. Run via sync-preview.sh.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

private = Path(sys.argv[1])
public = Path(sys.argv[2])

PUBLIC_REPO = "zkumar/healthcare-ai-book-preview"
PRIVATE_REPO = "zkumar/healthcare-ai-book"
COLAB_SVG = "https://colab.research.google.com/assets/colab-badge.svg"

chapters_src = private / "chapters"
docs = public / "docs"
config_file = public / "preview-chapters.txt"

slugs = [
    line.strip()
    for line in config_file.read_text().splitlines()
    if line.strip() and not line.lstrip().startswith("#")
]


def demote_headings(md: str) -> str:
    """Demote every markdown heading one level (# -> ##) so embedded docs nest cleanly."""
    return re.sub(r"^(#{1,5}) ", r"#\1 ", md, flags=re.MULTILINE)


# Wipe previously-synced chapter dirs (keep index.md, assets).
for d in docs.iterdir():
    if d.is_dir() and re.match(r"^\d{2}-", d.name):
        shutil.rmtree(d)

nav_entries = []  # (chapter_title, read_path, practitioner_path_or_None)

for slug in slugs:
    src_dir = chapters_src / slug
    src_md = src_dir / "chapter.md"
    if not src_md.exists():
        print(f"  WARNING: {slug}/chapter.md not found — skipping")
        continue

    dest_dir = docs / slug
    dest_dir.mkdir(parents=True, exist_ok=True)

    md = src_md.read_text()
    prac_src = src_dir / "practitioner"
    has_prac = prac_src.is_dir()

    # Rewrite the "## For Practitioners" section: strip it, then (if practitioner content
    # exists) we'll surface it via the nav sub-page instead of inline.
    if has_prac:
        md = re.sub(
            r"\n## For Practitioners\b.*?(?=\n---\n)",
            "\n## For Practitioners\n\nTechnical readers: a companion **[Practitioner Depth](practitioner.md)** "
            "page accompanies this chapter — regulatory data snapshots plus runnable, Colab-ready code.\n",
            md,
            flags=re.DOTALL,
        )
    else:
        md = re.sub(r"\n## For Practitioners\b.*?(?=\n---\n)", "", md, flags=re.DOTALL)

    # Neutral preview footer.
    md = re.sub(
        r"\*Chapter (\d+) of 21 ·[^\n]*\*",
        lambda m: (
            f"*Chapter {m.group(1)} · Preview edition. The complete book is in progress — "
            f"[share feedback](https://github.com/{PUBLIC_REPO}/issues).*"
        ),
        md,
    )
    (dest_dir / "index.md").write_text(md)

    # Figures.
    src_figs = src_dir / "figures"
    if src_figs.is_dir():
        shutil.copytree(src_figs, dest_dir / "figures", dirs_exist_ok=True)

    h1 = re.search(r"^#\s+(.+)$", md, flags=re.MULTILINE)
    title = h1.group(1).strip() if h1 else slug

    prac_rel = None
    if has_prac:
        prac_rel = f"{slug}/practitioner.md"
        code_dest = dest_dir / "code"
        code_dest.mkdir(exist_ok=True)

        parts = [f"# Practitioner Depth — {title.replace('Chapter ', 'Chapter ')}", ""]
        readme = prac_src / "README.md"
        if readme.exists():
            intro = readme.read_text()
            # Use the first non-heading, non-badge paragraph as the intro blurb.
            for para in intro.split("\n\n"):
                p = para.strip()
                if p and not p.startswith("#") and "colab-badge" not in p and not p.startswith("|"):
                    parts.append(p)
                    parts.append("")
                    break

        # Data snapshots (any *.md in practitioner/ except README.md).
        snapshot_files = sorted(p for p in prac_src.glob("*.md") if p.name != "README.md")
        if snapshot_files:
            parts.append("## Data Snapshots")
            parts.append("")
            for sf in snapshot_files:
                parts.append(demote_headings(sf.read_text().strip()))
                parts.append("")

        # Workshop tools (Excel templates from practitioner/files/*.xlsx).
        xlsx_dir = prac_src / "files"
        xlsx_files = sorted(xlsx_dir.glob("*.xlsx")) if xlsx_dir.is_dir() else []
        if xlsx_files:
            files_dest = dest_dir / "files"
            files_dest.mkdir(exist_ok=True)
            parts.append("## Workshop Tools (Excel)")
            parts.append("")
            parts.append("_Fillable templates with dropdowns, formula-driven verdicts, and conditional formatting._ "
                         "Open in Excel, Numbers, or Google Sheets and run with your team.")
            parts.append("")
            parts.append("| Template | Download |")
            parts.append("|---|---|")
            for xf in xlsx_files:
                shutil.copy(xf, files_dest / xf.name)
                title = xf.stem.replace("-", " ").title().replace("Ai ", "AI ")
                parts.append(f"| **{title}** | [⬇ `{xf.name}`](files/{xf.name}) |")
            parts.append("")

        # Code: copy .py, convert to .ipynb, render inline with Colab badge.
        py_files = sorted((prac_src / "code").glob("*.py")) if (prac_src / "code").is_dir() else []
        if py_files:
            parts.append("## Code")
            parts.append("")
            parts.append("_Tested and Colab-compatible. Click **Open in Colab** to run any sample in your browser — no setup._")
            parts.append("")
            for py in py_files:
                shutil.copy(py, code_dest / py.name)
                ipynb = code_dest / (py.stem + ".ipynb")
                subprocess.run(
                    ["jupytext", "--to", "ipynb", str(code_dest / py.name), "-o", str(ipynb)],
                    check=True, capture_output=True,
                )
                colab_url = (
                    f"https://colab.research.google.com/github/{PUBLIC_REPO}/blob/main/"
                    f"docs/{slug}/code/{ipynb.name}"
                )
                parts.append(f"### `{py.name}`")
                parts.append("")
                parts.append(f"[![Open In Colab]({COLAB_SVG})]({colab_url})")
                parts.append("")
                parts.append(f"[Download .py](code/{py.name}) · [Download notebook](code/{ipynb.name})")
                parts.append("")
                parts.append("```python")
                parts.append(py.read_text().rstrip())
                parts.append("```")
                parts.append("")

        (dest_dir / "practitioner.md").write_text("\n".join(parts))
        n_code = len(py_files)
        n_figs = len(list((dest_dir / "figures").glob("*"))) if (dest_dir / "figures").is_dir() else 0
        print(f"  {slug}: synced ({n_figs} figures, practitioner page + {n_code} code sample(s))")
    else:
        n_figs = len(list((dest_dir / "figures").glob("*"))) if (dest_dir / "figures").is_dir() else 0
        print(f"  {slug}: synced ({n_figs} figures, no practitioner content)")

    nav_entries.append((title, f"{slug}/index.md", prac_rel))

# --- Persistent assets and pages (always present, regardless of chapter selection) ---
assets_dest = docs / "assets"
assets_dest.mkdir(exist_ok=True)

# Book cover -> landing hero (web-optimized: cap longest edge at 1000px)
cover_src = private / "assets" / "cover" / "final_front_cover_practitioner_guide.png"
if cover_src.exists():
    cover_dest = assets_dest / "cover.png"
    shutil.copy(cover_src, cover_dest)
    if shutil.which("sips"):
        subprocess.run(["sips", "-Z", "1000", str(cover_dest)], capture_output=True)
    print("  cover image synced (optimized)")
else:
    print("  WARNING: cover image not found")

# Author photo — search assets/author.* and assets/author/*; normalize to docs/assets/author.png.
photo_candidates = [private / "assets" / f"author.{e}" for e in ("png", "jpg", "jpeg", "webp")]
author_dir = private / "assets" / "author"
if author_dir.is_dir():
    for e in ("png", "jpg", "jpeg", "webp"):
        photo_candidates.extend(sorted(author_dir.glob(f"*.{e}")))
photo_src = next((p for p in photo_candidates if p.exists()), None)
if photo_src:
    dest_photo = assets_dest / "author.png"
    shutil.copy(photo_src, dest_photo)
    # Web-optimize (macOS sips): cap longest edge at 900px, keeps retina sharpness.
    if shutil.which("sips"):
        subprocess.run(["sips", "-Z", "900", str(dest_photo)], capture_output=True)
    print(f"  author photo synced (from {photo_src.relative_to(private)})")
else:
    print("  author photo NOT found — About page shows a placeholder")

# Dedication — source of truth is DEDICATION.md in the private repo
ded_src = private / "DEDICATION.md"
if ded_src.exists():
    shutil.copy(ded_src, docs / "dedication.md")
    print("  dedication synced")

# Regenerate the nav block in mkdocs.yml.
mkdocs_yml = public / "mkdocs.yml"
text = mkdocs_yml.read_text()
nav_lines = ["nav:", "  - Home: index.md"]
for title, read_path, prac_path in nav_entries:
    safe_title = f'"{title}"' if ":" in title else title
    if prac_path:
        nav_lines.append(f"  - {safe_title}:")
        nav_lines.append(f"    - Read: {read_path}")
        nav_lines.append(f"    - Practitioner Depth: {prac_path}")
    else:
        nav_lines.append(f"  - {safe_title}: {read_path}")
# Persistent pages — always visible
nav_lines.append("  - About the Author: about.md")
if (docs / "dedication.md").exists():
    nav_lines.append("  - Dedication: dedication.md")
nav_block = "\n".join(nav_lines)

text = re.sub(r"# NAV-START.*?# NAV-END", f"# NAV-START\n{nav_block}\n# NAV-END", text, flags=re.DOTALL)
mkdocs_yml.write_text(text)
print(f"\nNav rebuilt with {len(nav_entries)} chapter(s).")

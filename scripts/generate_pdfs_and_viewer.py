#!/usr/bin/env python3
"""Generate one PDF per blog post and build an offline searchable viewer."""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

BASE_DIR = Path("data/extracted_blog")
POSTS_JSON = BASE_DIR / "posts.json"
PDF_DIR = BASE_DIR / "pdfs"
VIEWER_DIR = BASE_DIR / "viewer"
SEARCH_INDEX = BASE_DIR / "search-index.json"

TAG_RE = re.compile(r"<[^>]+>")
BLOCK_RE = re.compile(r"(?i)</(p|div|h[1-6]|li|ul|ol|blockquote|section|article|tr)>|<br\s*/?>")
WS_RE = re.compile(r"[ \t\r\f\v]+")
MULTI_NL_RE = re.compile(r"\n{3,}")
INVALID_FS_RE = re.compile(r"[^\w\-.]+", flags=re.UNICODE)


@dataclass
class Post:
    title: str
    published: str
    updated: str
    url: str
    slug: str
    year: str
    month: str
    labels: list[str]
    content_html: str
    content_text: str


def safe_name(value: str, fallback: str = "post") -> str:
    name = INVALID_FS_RE.sub("-", (value or "").strip().lower())
    name = re.sub(r"-+", "-", name).strip("-._")
    return name or fallback


def html_to_lines(html: str) -> list[str]:
    if not html:
        return []
    text = BLOCK_RE.sub("\n", html)
    text = TAG_RE.sub("", text)
    text = unescape(text)
    text = text.replace("\xa0", " ")
    text = WS_RE.sub(" ", text)
    text = re.sub(r"\n +", "\n", text)
    text = re.sub(r" +\n", "\n", text)
    text = MULTI_NL_RE.sub("\n\n", text)
    lines = [line.strip() for line in text.split("\n")]
    lines = [line for line in lines if line]
    return lines


def chunk_text(line: str, chunk_size: int = 1200) -> list[str]:
    if len(line) <= chunk_size:
        return [line]

    chunks: list[str] = []
    current = line
    while len(current) > chunk_size:
        split_at = current.rfind(" ", 0, chunk_size)
        if split_at < 200:
            split_at = chunk_size
        chunks.append(current[:split_at].strip())
        current = current[split_at:].strip()

    if current:
        chunks.append(current)
    return chunks


def build_styles() -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "PostTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#111827"),
            spaceAfter=12,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#4B5563"),
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor=colors.black,
            spaceAfter=8,
            wordWrap="CJK",
        ),
    }


def create_pdf(post: Post, output_path: Path, styles: dict[str, ParagraphStyle]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=post.title,
        author="almyalves.blogspot.com",
    )

    story = []
    story.append(Paragraph(escape(post.title or "(Sem titulo)"), styles["title"]))
    story.append(Paragraph(escape(f"Publicado: {post.published}"), styles["meta"]))
    story.append(Paragraph(escape(f"Atualizado: {post.updated}"), styles["meta"]))
    story.append(Paragraph(escape(f"URL original: {post.url}"), styles["meta"]))
    if post.labels:
        story.append(Paragraph(escape("Labels: " + ", ".join(post.labels)), styles["meta"]))

    story.append(Spacer(1, 0.3 * cm))

    lines = html_to_lines(post.content_html)
    if not lines and post.content_text:
        lines = [post.content_text]

    if not lines:
        lines = ["(Conteudo indisponivel)"]

    for line in lines:
        for chunk in chunk_text(line):
            story.append(Paragraph(escape(chunk), styles["body"]))

    doc.build(story)


def load_posts() -> list[Post]:
    raw = json.loads(POSTS_JSON.read_text(encoding="utf-8"))
    posts: list[Post] = []
    for item in raw:
        posts.append(
            Post(
                title=item.get("title", "(sem titulo)"),
                published=item.get("published", ""),
                updated=item.get("updated", ""),
                url=item.get("url", ""),
                slug=item.get("slug", ""),
                year=str(item.get("year", "")),
                month=str(item.get("month", "")),
                labels=item.get("labels", []) or [],
                content_html=item.get("content_html", "") or "",
                content_text=item.get("content_text", "") or "",
            )
        )
    return posts


def build_search_index(posts: list[Post]) -> list[dict[str, Any]]:
    index: list[dict[str, Any]] = []
    for post in posts:
        slug = safe_name(post.slug or post.title, fallback="post")
        pdf_rel = f"pdfs/{post.year}/{post.month}/{slug}.pdf"
        md_rel = f"posts/{post.year}/{post.month}/{slug}.md"

        lines = html_to_lines(post.content_html)
        body_text = "\n".join(lines).strip()
        if not body_text:
            body_text = post.content_text

        excerpt = body_text[:260].replace("\n", " ").strip()

        search_text = " ".join(
            [post.title, " ".join(post.labels), body_text]
        ).lower()

        index.append(
            {
                "title": post.title,
                "published": post.published,
                "updated": post.updated,
                "year": post.year,
                "month": post.month,
                "url": post.url,
                "slug": slug,
                "labels": post.labels,
                "excerpt": excerpt,
                "text": body_text,
                "search_text": search_text,
                "pdf": pdf_rel,
                "markdown": md_rel,
            }
        )

    return index


def write_viewer_files() -> None:
    VIEWER_DIR.mkdir(parents=True, exist_ok=True)

    index_html = """<!doctype html>
<html lang=\"pt-BR\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Acervo Offline - Blog Almy Alves</title>
  <link rel=\"stylesheet\" href=\"./styles.css\" />
</head>
<body>
  <header class=\"top\">
    <h1>Acervo Offline - Blog Almy Alves</h1>
    <p>Todos os artigos extraidos, com busca local e acesso aos PDFs.</p>
  </header>

  <section class=\"controls\">
    <input id=\"searchInput\" type=\"search\" placeholder=\"Pesquisar por titulo, trecho, label...\" />
    <select id=\"yearFilter\">
      <option value=\"\">Todos os anos</option>
    </select>
    <button id=\"clearBtn\" type=\"button\">Limpar</button>
  </section>

  <section class=\"summary\">
    <span id=\"countLabel\">Carregando...</span>
  </section>

  <main id=\"results\" class=\"results\"></main>

  <template id=\"cardTpl\">
    <article class=\"card\">
      <h2 class=\"title\"></h2>
      <p class=\"meta\"></p>
      <p class=\"labels\"></p>
      <p class=\"excerpt\"></p>
      <div class=\"actions\">
        <a class=\"btn pdf\" target=\"_blank\" rel=\"noopener\">Abrir PDF</a>
        <a class=\"btn md\" target=\"_blank\" rel=\"noopener\">Abrir Markdown</a>
        <a class=\"btn original\" target=\"_blank\" rel=\"noopener\">Post Original</a>
      </div>
    </article>
  </template>

  <script src=\"./app.js\"></script>
</body>
</html>
"""

    styles_css = """:root {
  --bg: #f6f7f9;
  --surface: #ffffff;
  --text: #1f2937;
  --muted: #6b7280;
  --accent: #0f766e;
  --accent-2: #155e75;
  --border: #e5e7eb;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
  background: radial-gradient(circle at top left, #eefbf8, var(--bg) 40%);
  color: var(--text);
}

.top {
  padding: 1.25rem 1rem 0.7rem;
  max-width: 1100px;
  margin: 0 auto;
}

.top h1 {
  margin: 0;
  font-size: 1.5rem;
}

.top p {
  margin: 0.4rem 0 0;
  color: var(--muted);
}

.controls {
  display: grid;
  grid-template-columns: 1fr 180px 120px;
  gap: 0.6rem;
  padding: 0.8rem 1rem;
  max-width: 1100px;
  margin: 0 auto;
}

.controls input,
.controls select,
.controls button {
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  border-radius: 10px;
  padding: 0.65rem 0.75rem;
  font-size: 0.95rem;
}

.controls button {
  cursor: pointer;
  background: linear-gradient(135deg, var(--accent), var(--accent-2));
  color: #fff;
  border: 0;
}

.summary {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1rem 0.8rem;
  color: var(--muted);
}

.results {
  max-width: 1100px;
  margin: 0 auto;
  padding: 0 1rem 1.5rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 0.8rem;
}

.card {
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 14px;
  padding: 0.9rem;
  box-shadow: 0 8px 20px rgba(15, 118, 110, 0.07);
}

.title {
  margin: 0;
  font-size: 1rem;
  line-height: 1.35;
}

.meta,
.labels {
  margin: 0.4rem 0 0;
  font-size: 0.82rem;
  color: var(--muted);
}

.excerpt {
  margin: 0.65rem 0 0;
  font-size: 0.9rem;
  line-height: 1.45;
}

.actions {
  margin-top: 0.75rem;
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
}

.btn {
  text-decoration: none;
  font-size: 0.8rem;
  border-radius: 8px;
  padding: 0.44rem 0.58rem;
  border: 1px solid var(--border);
  color: var(--text);
  background: #fff;
}

.btn.pdf { border-color: #86efac; }
.btn.md { border-color: #93c5fd; }
.btn.original { border-color: #fcd34d; }

@media (max-width: 740px) {
  .controls {
    grid-template-columns: 1fr;
  }
}
"""

    app_js = """const state = {
  posts: [],
  filtered: [],
};

const q = (sel) => document.querySelector(sel);
const resultsEl = q('#results');
const tpl = q('#cardTpl');
const searchInput = q('#searchInput');
const yearFilter = q('#yearFilter');
const clearBtn = q('#clearBtn');
const countLabel = q('#countLabel');

function normalize(str) {
  return (str || '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
}

function buildYearOptions(posts) {
  const years = [...new Set(posts.map((p) => p.year))].sort((a, b) => b.localeCompare(a));
  for (const y of years) {
    const opt = document.createElement('option');
    opt.value = y;
    opt.textContent = y;
    yearFilter.appendChild(opt);
  }
}

function render(posts) {
  resultsEl.innerHTML = '';
  const frag = document.createDocumentFragment();

  for (const post of posts) {
    const node = tpl.content.cloneNode(true);
    node.querySelector('.title').textContent = post.title;
    node.querySelector('.meta').textContent = `Publicado: ${post.published} | ${post.year}/${post.month}`;
    node.querySelector('.labels').textContent = post.labels?.length
      ? `Labels: ${post.labels.join(', ')}`
      : 'Labels: (nenhuma)';
    node.querySelector('.excerpt').textContent = post.excerpt || '(Sem trecho)';

    node.querySelector('.btn.pdf').href = `../${post.pdf}`;
    node.querySelector('.btn.md').href = `../${post.markdown}`;
    node.querySelector('.btn.original').href = post.url;

    frag.appendChild(node);
  }

  resultsEl.appendChild(frag);
  countLabel.textContent = `${posts.length} resultado(s) de ${state.posts.length} posts.`;
}

function applyFilters() {
  const term = normalize(searchInput.value.trim());
  const year = yearFilter.value;

  state.filtered = state.posts.filter((post) => {
    if (year && post.year !== year) return false;
    if (!term) return true;
    return normalize(post.search_text).includes(term);
  });

  render(state.filtered);
}

async function load() {
  const res = await fetch('../search-index.json');
  const posts = await res.json();
  state.posts = posts;
  state.filtered = posts;

  buildYearOptions(posts);
  render(posts);
}

searchInput.addEventListener('input', applyFilters);
yearFilter.addEventListener('change', applyFilters);
clearBtn.addEventListener('click', () => {
  searchInput.value = '';
  yearFilter.value = '';
  applyFilters();
});

load().catch((err) => {
  countLabel.textContent = 'Erro ao carregar o indice offline.';
  console.error(err);
});
"""

    viewer_files = [
        (VIEWER_DIR / "index.html", index_html),
        (VIEWER_DIR / "styles.css", styles_css),
        (VIEWER_DIR / "app.js", app_js),
    ]

    # Preserve manual improvements in the local viewer when rerunning extraction.
    for path, content in viewer_files:
        if not path.exists():
            path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate PDFs and local viewer")
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip PDF generation when the output file already exists",
    )
    args = parser.parse_args()

    if not POSTS_JSON.exists():
        raise SystemExit(f"Arquivo nao encontrado: {POSTS_JSON}")

    posts = load_posts()
    styles = build_styles()

    created = 0
    skipped = 0

    for i, post in enumerate(posts, start=1):
        slug = safe_name(post.slug or post.title, fallback=f"post-{i}")
        out = PDF_DIR / post.year / post.month / f"{slug}.pdf"

        if args.skip_existing and out.exists():
            skipped += 1
            continue

        create_pdf(post, out, styles)
        created += 1

        if i % 100 == 0 or i == len(posts):
            print(f"PDFs processados: {i}/{len(posts)}")

    index = build_search_index(posts)
    SEARCH_INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    write_viewer_files()

    print("\nConcluido.")
    print(f"Total de posts: {len(posts)}")
    print(f"PDFs criados nesta execucao: {created}")
    print(f"PDFs pulados (ja existentes): {skipped}")
    print(f"Diretorio PDFs: {PDF_DIR}")
    print(f"Indice de busca: {SEARCH_INDEX}")
    print(f"Viewer offline: {VIEWER_DIR / 'index.html'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

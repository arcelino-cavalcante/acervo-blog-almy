#!/usr/bin/env python3
"""Extract all posts from a Blogger blog feed and save organized files."""

from __future__ import annotations

import csv
import json
import re
import sys
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from pathlib import Path
from typing import Any

BLOG_URL = "https://almyalves.blogspot.com"
FEED_ENDPOINT = f"{BLOG_URL}/feeds/posts/default"
BATCH_SIZE = 150  # Blogger feed limit per request
OUTPUT_DIR = Path("data/extracted_blog")
POSTS_DIR = OUTPUT_DIR / "posts"


@dataclass
class Post:
    post_id: str
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
    word_count: int


TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def fetch_json(url: str) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def html_to_text(html: str) -> str:
    text = TAG_RE.sub(" ", html)
    text = unescape(text)
    text = WS_RE.sub(" ", text).strip()
    return text


def safe_name(value: str, fallback: str) -> str:
    name = re.sub(r"[^\w\-.]+", "-", value.strip().lower(), flags=re.UNICODE)
    name = re.sub(r"-+", "-", name).strip("-._")
    return name or fallback


def parse_post(entry: dict[str, Any]) -> Post:
    links = entry.get("link", [])
    alternate = next((l.get("href", "") for l in links if l.get("rel") == "alternate"), "")
    slug = alternate.rstrip("/").rsplit("/", 1)[-1] if alternate else entry["id"]["$t"].split("-")[-1]

    published = entry.get("published", {}).get("$t", "")
    updated = entry.get("updated", {}).get("$t", "")
    dt = datetime.fromisoformat(published.replace("Z", "+00:00")) if published else datetime.utcnow()
    year = f"{dt.year:04d}"
    month = f"{dt.month:02d}"

    content_html = entry.get("content", {}).get("$t", "")
    content_text = html_to_text(content_html)
    word_count = len(content_text.split()) if content_text else 0

    labels = [c.get("term", "") for c in entry.get("category", []) if c.get("term")]

    return Post(
        post_id=entry.get("id", {}).get("$t", ""),
        title=entry.get("title", {}).get("$t", "(sem titulo)").strip(),
        published=published,
        updated=updated,
        url=alternate,
        slug=slug,
        year=year,
        month=month,
        labels=labels,
        content_html=content_html,
        content_text=content_text,
        word_count=word_count,
    )


def write_markdown(post: Post) -> None:
    folder = POSTS_DIR / post.year / post.month
    folder.mkdir(parents=True, exist_ok=True)
    filename = safe_name(post.slug, fallback="post") + ".md"
    path = folder / filename

    labels = ", ".join(post.labels)
    safe_title = post.title.replace('"', "'")
    md = []
    md.append("---")
    md.append(f'title: "{safe_title}"')
    md.append(f"published: {post.published}")
    md.append(f"updated: {post.updated}")
    md.append(f"url: {post.url}")
    md.append(f"slug: {post.slug}")
    md.append(f"labels: [{labels}]")
    md.append("---")
    md.append("")
    md.append(f"# {post.title}")
    md.append("")
    md.append(f"Publicado em: {post.published}")
    md.append("")
    md.append(f"Link original: {post.url}")
    md.append("")
    md.append("## Conteudo (HTML original)")
    md.append("")
    md.append(post.content_html)
    md.append("")

    path.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    POSTS_DIR.mkdir(parents=True, exist_ok=True)

    first_url = f"{FEED_ENDPOINT}?alt=json&start-index=1&max-results=1"
    first = fetch_json(first_url)
    feed = first.get("feed", {})
    total = int(feed.get("openSearch$totalResults", {}).get("$t", 0))

    if total == 0:
        print("Nenhum post encontrado no feed.")
        return 1

    print(f"Total de posts reportados no feed: {total}")

    posts: list[Post] = []
    start = 1
    while start <= total:
        params = urllib.parse.urlencode({
            "alt": "json",
            "start-index": start,
            "max-results": BATCH_SIZE,
        })
        url = f"{FEED_ENDPOINT}?{params}"
        data = fetch_json(url)
        entries = data.get("feed", {}).get("entry", [])

        if not entries:
            break

        for entry in entries:
            posts.append(parse_post(entry))

        print(f"Coletados {len(posts)} / {total} posts...")
        start += len(entries)

        # Safety break against accidental infinite loops
        if len(entries) == 0:
            break

    # Deduplicate by URL while preserving order
    seen: set[str] = set()
    unique_posts: list[Post] = []
    for p in posts:
        key = p.url or p.post_id
        if key in seen:
            continue
        seen.add(key)
        unique_posts.append(p)

    posts = unique_posts

    # JSON export
    json_path = OUTPUT_DIR / "posts.json"
    json_payload = [
        {
            "post_id": p.post_id,
            "title": p.title,
            "published": p.published,
            "updated": p.updated,
            "url": p.url,
            "slug": p.slug,
            "year": p.year,
            "month": p.month,
            "labels": p.labels,
            "word_count": p.word_count,
            "content_html": p.content_html,
            "content_text": p.content_text,
        }
        for p in posts
    ]
    json_path.write_text(json.dumps(json_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # CSV export (lighter metadata)
    csv_path = OUTPUT_DIR / "posts.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "title",
                "published",
                "updated",
                "url",
                "slug",
                "year",
                "month",
                "labels",
                "word_count",
            ],
        )
        writer.writeheader()
        for p in posts:
            writer.writerow(
                {
                    "title": p.title,
                    "published": p.published,
                    "updated": p.updated,
                    "url": p.url,
                    "slug": p.slug,
                    "year": p.year,
                    "month": p.month,
                    "labels": " | ".join(p.labels),
                    "word_count": p.word_count,
                }
            )

    # Markdown per post
    for p in posts:
        write_markdown(p)

    # Index file
    index_path = OUTPUT_DIR / "README.md"
    years = sorted({p.year for p in posts})
    min_date = min((p.published for p in posts if p.published), default="")
    max_date = max((p.published for p in posts if p.published), default="")

    lines = [
        "# Extracao do blog almyalves.blogspot.com",
        "",
        f"Total de posts extraidos: **{len(posts)}**",
        f"Periodo encontrado: **{min_date}** ate **{max_date}**",
        "",
        "## Arquivos gerados",
        "",
        "- `posts.json`: dataset completo com conteudo HTML e texto limpo.",
        "- `posts.csv`: inventario tabular dos artigos.",
        "- `posts/<ano>/<mes>/*.md`: um markdown por artigo.",
        "",
        "## Anos encontrados",
        "",
        ", ".join(years),
        "",
    ]
    index_path.write_text("\n".join(lines), encoding="utf-8")

    print("\nExtracao concluida.")
    print(f"Posts unicos salvos: {len(posts)}")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    print(f"MDs:  {POSTS_DIR}")
    print(f"Index:{index_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

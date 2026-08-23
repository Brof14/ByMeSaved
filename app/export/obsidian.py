from pathlib import Path
import re
import shutil
import tempfile
import zipfile

from app.config import settings
from app.db.repository import list_notes

def slug(value: str) -> str:
    value = re.sub(r"[^\w\- ]+", "", value, flags=re.UNICODE).strip()
    return re.sub(r"\s+", "-", value)[:100] or "note"

async def export_user(user_id: int) -> Path:
    notes = await list_notes(user_id, 10000)
    base = Path(settings.export_dir)
    base.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f"kb-{user_id}-", dir=base))
    try:
        for n in notes:
            category = slug(n["category"] or "other")
            path = tmp / category
            path.mkdir(parents=True, exist_ok=True)
            title = n["title"] or f"Note {n['id']}"
            tags = ", ".join(n["tags"] or [])
            content = f"""---
id: {n['id']}
title: {title!r}
created: {n['created_at'].date().isoformat()}
category: {n['category'] or 'other'}
tags: [{tags}]
---

# {title}

## Summary
{n['summary'] or ''}

## Original
{n['content']}

"""
            if n["source_url"]:
                content += f"## Source\n{n['source_url']}\n"
            (path / f"{slug(title)}-{n['id']}.md").write_text(content, encoding="utf-8")
        archive = base / f"knowledge-export-{user_id}.zip"
        if archive.exists():
            archive.unlink()
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for p in tmp.rglob("*"):
                if p.is_file():
                    z.write(p, p.relative_to(tmp))
        return archive
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

from __future__ import annotations
import re
from bs4 import BeautifulSoup
import html2text

html_converter = html2text.HTML2Text()
html_converter.ignore_links = True
html_converter.ignore_images = True
html_converter.body_width = 0

_control_re = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def html_to_text(html: str | None) -> str:
    if not html:
        return ""
    try:
        text = html_converter.handle(html)
    except Exception:
        text = BeautifulSoup(html, "lxml").get_text("\n")
    text = _control_re.sub("", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_get(d: dict, *path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur

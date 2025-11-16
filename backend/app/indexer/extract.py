from bs4 import BeautifulSoup
import re
from typing import Tuple, List

def html_to_text_and_title(html: str) -> Tuple[str, str]:
    """
    Convert a raw HTML page into (plain_text, title).

    - Strips navigation and layout elements (nav, header, footer, common sidebar classes).
    - Removes script/style/noscript tags.
    - Extracts the <title> from the <head> if present; otherwise returns "".
    - Returns all visible text as a single string, using '\n' between blocks and
      collapsing 3+ consecutive newlines into 2.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Try to hide nav/sidebars (common doc sites)
    for sel in ["nav", "header", "footer", ".toc", ".sidebar", ".sphinxsidebar", ".bd-sidebar"]:
        for tag in soup.select(sel):
            tag.decompose()

    title = soup.title.get_text(strip=True) if soup.title else ""
    # remove scripts/styles
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    # normalize whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, title

def chunk_text_heading_aware(text: str, max_len: int = 1000) -> List[str]:
    """
    Split text into reasonably sized chunks:
    - First split on blank lines (paragraph / section boundary).
    - Each block becomes its own chunk if it fits within max_len.
    - If a block is longer than max_len:
        - Try splitting into sentences.
        - If still too long, split by words into character-length-based chunks.
    """

    def split_long_block(block: str) -> List[str]:
        # Try sentence-level split first.
        sentences = re.split(r"(?<=[.!?])\s+", block)
        # If we didn't really split (no punctuation), fall back to word-level
        if len(sentences) == 1:
            words = block.split()
            chunks = []
            buf = []
            total = 0
            for w in words:
                # +1 for space
                if total + len(w) + (1 if buf else 0) > max_len and buf:
                    chunks.append(" ".join(buf))
                    buf = [w]
                    total = len(w)
                else:
                    buf.append(w)
                    total += len(w) + (1 if buf[:-1] else 0)
            if buf:
                chunks.append(" ".join(buf))
            return chunks

        # We have multiple sentences, pack them into chunks up to max_len
        chunks = []
        buf = []
        total = 0
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            # +1 for space/newline
            if total + len(s) + (1 if buf else 0) > max_len and buf:
                chunks.append(" ".join(buf))
                buf = [s]
                total = len(s)
            else:
                buf.append(s)
                total += len(s) + (1 if buf[:-1] else 0)
        if buf:
            chunks.append(" ".join(buf))
        return chunks

    # Split on blank lines to get coarse sections
    blocks = re.split(r"\n\s*\n", text)
    chunks: List[str] = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if len(block) <= max_len:
            # Make each block its own chunk
            chunks.append(block)
        else:
            # Split further
            chunks.extend(split_long_block(block))

    return chunks
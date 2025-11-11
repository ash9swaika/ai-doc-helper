# backend/app/scrape.py
from bs4 import BeautifulSoup  # add 'beautifulsoup4' to pyproject
import urllib.request, urllib.parse, os, time

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent":"ai-doc-helper"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.read().decode("utf-8", errors="ignore")

def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    # remove nav/footer/script/style
    for s in soup(["script","style","nav","footer"]): s.decompose()
    return soup

def extract_blocks(soup):
    # naive: take headings + following paragraphs
    blocks = []
    current = []
    for el in soup.find_all(["h1","h2","h3","p","li","pre","code"]):
        tag = el.name
        text = " ".join(el.get_text(" ", strip=True).split())
        if not text: continue
        if tag in ("h1","h2","h3") and current:
            blocks.append(" ".join(current)); current=[]
        current.append(text)
    if current: blocks.append(" ".join(current))
    return blocks

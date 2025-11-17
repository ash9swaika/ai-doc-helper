from app.indexer.extract import html_to_text_and_title, chunk_text_heading_aware

def test_html_to_text_extracts_title():
    "Test Title Extraction from HTML"
    html = "<html><head><title>Test Page</title></head><body>Hello</body></html>"
    _, title = html_to_text_and_title(html)
    assert title == "Test Page"

def test_html_to_text_removes_nav_sidebar():
    html = """
    <html>
      <body>
        <nav>Menu</nav>
        <div>Main content here</div>
      </body>
    </html>
    """
    text, _ = html_to_text_and_title(html)
    assert "Menu" not in text
    assert "Main content here" in text

def test_html_to_text_removes_script_tags():
    html = """
    <html>
      <body>
        <script>alert('x')</script>
        <style>.hidden{}</style>
        <p>Visible text</p>
      </body>
    </html>
    """
    text, _ = html_to_text_and_title(html)
    assert "alert" not in text
    assert "Visible text" in text

def test_html_to_text_normalizes_whitespace():
    "Test if it handles whitespace properly"
    html = "<html><body><p>A</p><p>B</p></body></html>"
    text, _ = html_to_text_and_title(html)
    # Should not contain excessive blank lines
    assert "\n\n\n" not in text


def test_chunking_short_text():
    text = "Short text"
    chunks = chunk_text_heading_aware(text, max_len=50)
    assert chunks == ["Short text"]


def test_chunking_long_text_into_multiple_chunks():
    text = "A " * 2000  # very long
    chunks = chunk_text_heading_aware(text, max_len=200)
    assert len(chunks) > 1
    for c in chunks:
        assert len(c) <= 250  # small buffer allowed

def test_chunking_respects_blank_lines():
    text = "Section1\nline\n\nSection2\nline2"
    chunks = chunk_text_heading_aware(text, max_len=100)
    assert "Section1" in chunks[0]
    assert "Section2" in chunks[1]

def test_chunking_splits_sentences_for_long_blocks():
    text = "Sentence one. Sentence two. Sentence three." * 20  # very long
    chunks = chunk_text_heading_aware(text, max_len=100)
    assert len(chunks) > 1



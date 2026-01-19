# scripts/strip_py.py
import tokenize
from io import BytesIO
from pathlib import Path

SRC = Path("backend/app")
DST = Path("back")

def strip_comments(code):
    tokens = tokenize.tokenize(BytesIO(code.encode()).readline)
    return "".join(
        t.string for t in tokens
        if t.type != tokenize.COMMENT
    )

for p in SRC.rglob("*.py"):
    out = DST / p.relative_to(SRC)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # odczyt UTF-8
    original_text = p.read_text(encoding="utf-8", errors="ignore")  # <- 'ignore' pomija problematyczne znaki
    
    cleaned = strip_comments(original_text)
    
    # zapis UTF-8
    out.write_text(cleaned, encoding="utf-8")

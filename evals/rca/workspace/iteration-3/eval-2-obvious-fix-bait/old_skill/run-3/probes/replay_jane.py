"""Replay the three logged searches from BUG_REPORT.md against a store holding Jane's typed email."""
import sys
sys.path.insert(0, sys.argv[1])
from app import db, search
db.reset()
db._NEXT_ID = 8412
db.insert("Jane.smith@gmail.com", "Jane Smith")
for q in ["Jane.Smith@gmail.com", "jane.smith@gmail.com", "Jane.smith@gmail.com"]:
    print(f"{q:24} -> {search.search_by_email(q)}")

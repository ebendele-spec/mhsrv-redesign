#!/usr/bin/env python3
"""The search index now lives in the allowlisted inventory.json catalog."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'inventory.json'
data=json.loads(p.read_text())
print(f'Search catalog ready: {len(data["items"]):,} units. Import a new feed with tools/build-inventory.py to refresh.')

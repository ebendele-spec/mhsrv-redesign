#!/usr/bin/env python3
"""Import a daily private feed and rebuild the site. Backward-compatible command."""
import argparse,subprocess,sys
from pathlib import Path
from datetime import date
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('feed',type=Path)
p.add_argument('--date',default=date.today().isoformat())
a=p.parse_args()
subprocess.run([sys.executable,str(root/'tools/import_inventory.py'),str(a.feed),'--date',a.date],check=True)
subprocess.run([sys.executable,str(root/'tools/build-site.py')],check=True)

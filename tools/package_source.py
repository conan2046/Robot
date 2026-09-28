#!/usr/bin/env python3
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'robot-showcase-source.zip'
EXCLUDE={'.git','.lovable','node_modules','dist','__pycache__','.DS_Store','roadmap.md','robot-showcase-source.zip'}
def skip(p):return any(part in EXCLUDE for part in p.parts)
if OUT.exists():OUT.unlink()
with zipfile.ZipFile(OUT,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
    for p in ROOT.rglob('*'):
        if p.is_file() and not skip(p.relative_to(ROOT)):
            z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
print(OUT)

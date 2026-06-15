import shutil
from pathlib import Path
path = Path(r"c:\Users\USER\Documents\My Projects\CourtVisioAi\.emergent")
print('exists', path.exists())
if path.exists():
    shutil.rmtree(path)
    print('removed')
else:
    print('not found')

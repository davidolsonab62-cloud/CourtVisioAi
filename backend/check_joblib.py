import sys
import subprocess
from pathlib import Path
out = Path(__file__).parent / 'check_joblib.txt'
try:
    import joblib
    out.write_text(f'JOBLIB_OK {joblib.__version__}\nPYTHON {sys.executable}\n')
except Exception as e:
    out.write_text(f'JOBLIB_ERROR {e}\nPYTHON {sys.executable}\n')

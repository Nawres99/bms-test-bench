# behave loads this before the step modules. Put the repo root on sys.path so the
# steps can do `from bms... import ...` when behave is run from the project root.
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

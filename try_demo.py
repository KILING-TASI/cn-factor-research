# SPDX-License-Identifier: MIT
"""Source-ZIP teaching without installation or sibling repositories."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from cn_factor_research.__main__ import main
raise SystemExit(main(['demo',*sys.argv[1:]]))

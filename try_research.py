# SPDX-License-Identifier: MIT
"""Source-only teaching entry; no installation or sibling repository needed."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from cn_factor_research.__main__ import main
raise SystemExit(main(['research-demo',*sys.argv[1:]]))

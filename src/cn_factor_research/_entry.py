# SPDX-License-Identifier: MIT
"""Locate only this distribution's bundled public teaching resources."""
from pathlib import Path
import sys

def resources():
    source=Path(__file__).resolve().parents[2]
    if (source/'README.md').is_file() and (source/'examples').is_dir():return source
    shared=Path(sys.prefix)/'share/cn-factor-research'
    if shared.is_dir():return shared
    raise ValueError('缺少本仓资源，请安装完整wheel或完整源码；不向其他仓库寻找缓存。')

def main(argv=None):
    from .__main__ import main as run
    return run(argv)

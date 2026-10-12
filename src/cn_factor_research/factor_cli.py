# SPDX-License-Identifier: MIT
from .review_io import cli
def main(argv=None):
    import sys
    from .factor_research import panel,trials
    previous=sys.argv[:]
    try:
        if argv is not None:sys.argv=['cn-factor-research',*argv]
        return cli({'panel':panel,'trials':trials},'因子面板与试验留档')
    finally:sys.argv[:]=previous

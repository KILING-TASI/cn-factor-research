# Quantitative factor research

Independent candle rules, CNN regression, paired validation, factor panels and trial records. Python 3.10+, no mandatory runtime dependencies. PyTorch is optional for training and inference.

[中文说明](README.md) · [Release v0.2.1](https://github.com/KILING-TASI/factor-research/releases/tag/v0.2.1)

Current release: **v0.2.1 · regular release**.

Download the [complete source ZIP](https://github.com/KILING-TASI/factor-research/releases/download/v0.2.1/cn-factor-research-v0.2.1-source.zip) and run `python try_demo.py --out-dir reports/first-demo`. Install with `python -m pip install .`; use `cn-factor-research --help`. Training and inference require `.[cnn]`.

The package does not require sibling repositories, author caches or live data access. Teaching examples are synthetic. Scores are not probabilities; descriptive gross returns are not executable portfolio returns. See [migration](MIGRATION.md), [CNN contracts](CNN_RESEARCH.md), [pattern rules](PATTERN_RESEARCH.md) and [rights](THIRD_PARTY_NOTICES.md).

Daily research: eight explicit baselines, frozen paired audits, optional industry/size residuals, event outcomes and method/data readiness. Run `python try_research.py --out-dir reports/first-research`; see [daily research](DAILY_RESEARCH.md). High-frequency, fundamental and behavioral models remain unimplemented.

Repository: `factor-research`. The distribution, CLI and Skill retain `cn-factor-research`; the Python module remains `cn_factor_research`. These compatibility names and the v0.2.1 archive filename are intentional. Clone `https://github.com/KILING-TASI/factor-research.git`, then enter `factor-research`. CLI installation does not register the Skill.

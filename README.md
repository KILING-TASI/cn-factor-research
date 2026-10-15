# 量化因子研究

从声明行情生成信号，核对K线形态、CNN预测与因子面板，保留参数、模型和证据缺口。

[原创代码 MIT](LICENSE) · [发行说明](https://github.com/KILING-TASI/factor-research/releases/tag/v0.2.1) · [运行检查](https://github.com/KILING-TASI/factor-research/actions) · [English](README.en.md)

当前发布：**v0.2.1 · 普通发行版**。Python **3.10+**；基础功能无必需第三方依赖，训练和预测按需安装 `[cnn]`。

## 能解决什么问题

**这个信号有哪些依据？加入形态信息后，预测误差是否变化？**

当前提供8种日频因子、行业市值中性化验收、事件统计与方法准备核对，以及11种显式K线规则、按期限条件统计、五通道CNN、滚动验证、三路线同样本对照，以及因子面板和试验台账。它可以单独使用，不需要安装PDE、数据仓或工作台。

| 需要准备 | 会得到什么 |
|---|---|
| OHLCV、当期股票池、复权/单位/时点依据；研究效果还需随后收益 | 形态命中与前置条件、回归得分、分层相关、对照误差、模型与试验记录 |

## 快速开始

下载[完整源码ZIP](https://github.com/KILING-TASI/factor-research/releases/download/v0.2.1/cn-factor-research-v0.2.1-source.zip)，解压后在该目录运行：

```console
python try_demo.py --out-dir reports/first-demo
```

命令会给出HTML路径。教学使用本仓原创合成样本，不自动下载真实行情，不需要PyTorch；重复运行使用新目录。

使用Git时运行 `git clone https://github.com/KILING-TASI/factor-research.git`，再进入 `factor-research` 目录。

量价研究的完整合成教学：`python try_research.py --out-dir reports/first-research`。覆盖因子、冻结验收、事件与缺口，基础功能仍无必需第三方依赖。

## 使用自己的资料

命令行：源码目录运行 `python -m pip install .`，查看 `cn-factor-research --help`。下载wheel时可用 `python -m pip install 路径/cn_factor_research-0.2.1-py3-none-any.whl`。

CNN另装 `python -m pip install ".[cnn]"`；CPU安装细节见 [CNN研究](CNN_RESEARCH.md)。不会自动安装或联网取数；安装依赖本身可能联网。

助手Skill：按 [SKILL.md](SKILL.md) 注册并保留完整资源；安装CLI不会自动注册Skill。

| 身份 | 名称 |
|---|---|
| GitHub仓库 | `factor-research` |
| Python发行包 / 主要命令 / Skill（保留兼容） | `cn-factor-research` |
| Python模块 | `cn_factor_research` |

仓库已更名为 `factor-research`；安装包、命令和 Skill 名称保留兼容。v0.2.1 的下载文件名也保留原名，使用上方链接即可。

先确认来源、日期、当期成员、成交量股数和价格口径，再运行 `cnn validate` 或 `pattern identify`。当前沪深300名单不能回填全部历史。用户自带文件即可研究；数据仓提供可选取数，工作台提供可选组织与解释。

## 能力与边界

| 已实现 | 范围 |
|---|---|
| `daily generate` | 8种日频因子、窗口新高与高低位放量事件；明确原始口径 |
| `audit review` | 同样本冻结切分、行业市值残差、因子重叠、条件换手与成本估算 |
| `event study` | 正负方向、重复触发、各期限已知/未知结果、匹配基准 |
| `plan review` | 软件与数据分开；高频、基本面与行为方法未实现时明确阻断 |
| `pattern identify/study` | 11种原创规则；外形与趋势分开；毛收益、基准及CN成交缺口 |
| `cnn` | CPU回归、时间清洗、训练期标准化、滚动验证、冻结预测、实测标签桥接与几何对照 |
| `panel/trials` | 声明因子的逐截面相关/分层、试验状态与选型记录 |

得分不是上涨概率。教学验收不认证真实A股效果，毛收益不是账户净值。当前没有完整基本面、行为金融和高频因子库、基准超额训练标签、分类网络、交易撮合、显著性/DSR/PBO或完整消融平台；没有自动认证复权、退市覆盖或可成交。

组合敞口、成本、资金占用和约束进入 [PDE](https://github.com/KILING-TASI/portfolio-decision-engine)。独立计算结果可以按明确接口导出，不要求运行时安装PDE。

## 文档与维护

- [日频因子、统一验收和事件接口](DAILY_RESEARCH.md)
- [76份参考文件及核对状态](RESEARCH_LIBRARY.json)（不是76套已实现方法）
- [CNN契约与调用](CNN_RESEARCH.md)
- [形态规则、统计与对照](PATTERN_RESEARCH.md)
- [面板与试验留档](FACTOR_REVIEW.md)
- [与PDE的迁移和兼容](MIGRATION.md)
- [已实现家族及状态](catalog.json)
- [版本记录](CHANGELOG.md)
- [第三方与数据权利](THIRD_PARTY_NOTICES.md)
- [安全反馈](SECURITY.md)

原创代码MIT，第三方依赖保留其许可，来源数据不随代码许可转移权利。仓库只含合成教学资料，不包含作者真实行情缓存或官方指数名单。

## 公开底稿验收

[覆盖登记](PUBLIC_VALIDATION.json)区分公开事实、混合教学与尚缺样本。运行 `python tools/verify_public_validation.py --run-checks --output reports/public-validation-v1.json` 可核对冻结文本与已登记反例；重复运行使用新文件。通过不表示重新认证原文或真实市场效果，未取得的样本仍列为缺口。

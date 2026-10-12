# 因子面板与试验留档

`cn-factor-research panel --input examples/expansion-teaching/panel.json --out-dir reports/panel` 核对信号、因子、股票池和收益可得时点，输出逐截面IC/rank IC、保持并列值同组的分层毛收益及未年化ICIR。数据不足或因子常量时相关未知，不输出概率。

`cn-factor-research trials --input examples/expansion-teaching/trials.json --out-dir reports/trials` 保存声明的成功、失败、阻断与选型记录；训练及标签结束必须早于测试开始，需明确测试未参与选型。它不认证仓库外尝试次数或完整独立性，也不计算DSR/Reality Check。

两者只用标准库。输入沿用PDE既有契约，字段示例随包提供；新 `factor-review/2` 还需 `factorId/factorVersion/factorDefinition/factorSource`。CLI也保留 `factor panel/trials` 别名。结果保存输入、摘要、HTML和回执，旧目录不覆盖。

这些统计不是成本净收益、可投性或策略盈利认证。CNN实测标签桥接输出 `panelInput`，可单独保存后再作面板审查；回顾性模拟不能伪造普通历史可得因子。

# 早盘低开反抽做空（SPY）— 第一阶段回测

把"开盘一小时、低开后冲高遇阻做空 SPY 0DTE put"写成固定规则，用 SPY 1 分钟 K 线回测，
先回答**信号本身在标的上有没有优势**。结果单位是 R（盈亏 ÷ 初始止损距离），**不是期权盈亏**。

与 LLM 多智能体框架完全独立，不需要任何 LLM API key。

## 规则

| 条件 | 规则化定义（参数见 `config.py`） |
|---|---|
| ① 低开 | 9:30 开盘价比昨收低 0.15%–2% |
| ② 价涨量缩 | 从当日低点起的反弹中，最后 3 根 K 线的**相对成交量**均值 ≤ 前 3 根的 80%。相对成交量 = 成交量 ÷ 过去 20 天同一分钟的成交量中位数，用来排除开盘后成交量自然衰减的干扰 |
| ③ 供给区遇阻 | 开盘前算好的价位 ± 0.05%：昨收、昨低、昨高、昨日成交量分布的 POC / VAH / VAL、盘前高点。反弹触及区域且收盘没站上去，然后一根阴线收在区域下方并跌破前一根低点 |
| 入场 | 信号 K 线的下一根开盘价，只在 9:35–10:30 之间入场，每天最多一笔 |
| 止损 | max(反弹高点, 区域上沿) + 0.03%；止损距离不在 0.05%–0.6% 的不做 |
| 止盈 | 1R 平一半并把止损移到保本，2R 平剩下一半；12:00 还没走完就全部平掉 |
| 成本 | 每次成交 0.002% 滑点（约 1 美分） |

同时跑 5 个版本，看每加一个条件到底有没有用：`gap_only`、`gap+exhaustion`、`gap+zone`、
`full`，以及对照组 `control: no gap-down`（非低开日用同一套量缩 + 供给区规则）。

## 运行

```bash
pip install pandas requests yfinance matplotlib tabulate

# 完整回测（Alpaca 分钟线，2019 至今）
export ALPACA_API_KEY_ID=...        # Alpaca 模拟盘的 key 就行
export ALPACA_API_SECRET_KEY=...
python -m tradingagents.strategies.opening_reversal --source alpaca --start 2019-01-01

# 不要 key 的冒烟测试（Yahoo 最近 60 天 5 分钟线，样本太少，只验证流程）
python -m tradingagents.strategies.opening_reversal --source yfinance --interval 5m

# 单元测试（合成数据，不联网）
python -m pytest tests/test_opening_reversal.py -q
```

输出在 `results/opening_reversal/`：`REPORT.md`、`summary.csv`、每个版本的逐笔交易 CSV、
累计 R 曲线图。Alpaca 数据按月缓存在 `tradingagents/dataflows/data_cache/intraday/`。

## 已知局限

- "买盘衰竭"只用了成交量近似，真正的足迹图（主动买卖量、delta 背离、吸收）要逐笔成交加买卖盘数据，属于第二阶段。
- "有承接就止盈"用固定的 R 倍数代替了，同样要订单流数据才能做。
- 同一根 K 线里同时碰到止损和止盈时，按先止损计算（偏保守）。
- 期权盈亏、价差、选多少 delta 的合约是第三阶段，要用真实的 0DTE 历史报价。

仅作研究，不构成投资建议。

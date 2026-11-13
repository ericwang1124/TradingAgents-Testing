# SPY / ES 跳空回补统计与开盘类型（Market Profile / Auction Market Theory）研究笔记

> 研究范围：SPY / ES / SPX 的 gap-fill 统计、Dalton 开盘类型（Open Drive / Open Test Drive / Open Rejection Reverse / Open Auction）、Opening Range / Initial Balance 统计、80% rule 等拍卖理论规则的“宣称 vs 实测”。
>
> **方法说明（重要）**：本沙箱内 WebFetch 对 thetrading.tools、statoasis.com、tradingstats.net、tradethatswing.com 均 DNS 解析失败（不在网络白名单内），因此以下数字几乎全部来自 WebSearch（extended 模式）返回的页面摘要，而非全文核对。凡是摘要措辞含糊或互相矛盾之处均已标注。不同来源的 gap 定义（close-to-open vs 开在前日区间外的 "full gap"）、fill 定义（触及前收 vs 收盘前回补 vs 最终任何时候回补）、样本期差异极大，数字之间**不可直接比较**。
>
> 与用户回测的关系：用户在 SPY 1 分钟（2019-2026）上测试“gap-down → 反弹进入供给区（前收、前日低点、VA、盘前高点）且量能衰减 → 首小时做空/买 0DTE put”，结果 Sharpe ≈ 0 或为负。下文多处结论与该结果一致（见各节 Inferences）。

---

## 问题 1：SPY/ES 跳空当日回补概率（按幅度、方向、开盘位置、星期、2020 年后变化）

### Takeaway
所有来源一致的结论只有一条：**gap 越大，当日回补概率越低**（以 ATR 归一化后这一关系最清晰：<0.3×ATR 约 78% 当日回补，>1.2×ATR 仅约 8%）；**gap-down 的当日回补率略高于 gap-up**；开在前日区间内的 gap 比开在区间外的更容易回补（约 70% vs 43–47%）；而且 SPY 当日回补率在 2014 年后明显下降（up gap 58%→43%，down gap 61%→48%）。“回补概率高”本身不等于有可交易优势——多个回测显示 gap fade 在扣除成本后接近盈亏平衡或亏损，大 gap 顺势方向反而略优。

### Cited Findings

**A. 按 gap 绝对/百分比幅度（SPY）**
- SPY 自 1993 年起，0.1–0.25% 的 up-gap（n=1,210）当日回补 78%，5 个交易日内回补 91%；作者自己指出 0.15% 的 gap 只需要 0.15% 的波动就能回补，而日均波幅是其数倍，因此高回补率本身不是 edge — [Snappchart（引用 thetrading.tools 数据）](https://www.snappchart.app/blog/pattern-library/types-of-gaps)
- 同一数据集：1–2% 的 up-gap 当日回补约 26%，5 日内回补 53%（n=291）；1% 以上的 gap 当日回补不到三分之一 — [thetrading.tools Gap Analysis](https://www.thetrading.tools/gap-analysis)（全文未能抓取，数字来自搜索摘要；down-gap 分桶数据未能获得）
- SPY 日线自 2001 年：0.25–0.5% 的 gap 当日回补率 up 60% / down 67%；≥2% 的 gap 降至 up 34% / down 39%；≥1% 的 gap 约 up 1/3、down 40%。fill 定义 = gap 日的最低价（up gap）或最高价（down gap）触及前收 — [Kagels Trading: Gap Trading](https://kagels-trading.com/blog/gap-trading/)
- 同一来源的**时代分段**：当日回补率 2001–2013 年 up 58.1% / down 60.9%，2014–2026 年降至 up 43.1% / down 47.7%；样本表述为 3,523 个 SPY gap（1,967 up / 1,556 down）（原文措辞是否为“已回补的 gap 数”不清楚）— [Kagels Trading](https://kagels-trading.com/blog/gap-trading/)
- StatOasis：1993 年以来 8,397 个 S&P 500 开盘 gap，down-gap 回补 98%、up-gap 94%，“通常在当日”；最小两档 95%/96%，>2% 降至 83%；up 与 down gap 之后 5 日漂移幅度相近（“direction is noise”）；>2% 的 gap 次日波动更大（“size is the signal”）；其主页另称“两个方向都不能跑赢随机入场”。**该回补率远高于其他来源，很可能是“最终任何时候回补”而非当日回补，不可与其他数字直接比较** — [StatOasis: S&P 500 Opening Gaps](https://statoasis.com/overfit/research/sp500-opening-gaps)；StatOasis 另一篇称按 ATR 分桶后次日平均收益并不随幅度上升 — [StatOasis: Big Range Days](https://statoasis.com/overfit/research/sp500-big-range-days)
- SwingTradeBot（SPY）：1 个交易日内回补 19.9%，5 个交易日内 54.1%，回补中位时间 5 个交易日（其 gap 定义很可能是开在前日高低点之外的 full gap，与 close-to-open gap 不同）— [SwingTradeBot SPY Gaps](https://swingtradebot.com/equities/SPY/gaps)
- QuantifiedStrategies：bullish gap 28% 回补（204 例）、bearish gap 33% 回补（202 例）（上下文/幅度条件在摘要中不清楚）；跌幅 < -0.7% 的大 gap-down 买入开盘期望为 -0.11%/笔 — [QuantifiedStrategies: Gap Trading Strategies](https://www.quantifiedstrategies.com/gap-trading-strategies/)；[Gap Fill Trading Strategies](https://www.quantifiedstrategies.com/gap-fill-trading-strategies/)

**B. 按 ATR 归一化（ES/NQ 期货）**
- tradingstats.net 以 14 日 ATR 分档：tiny <0.3×ATR 收盘前回补约 78%；small 0.3–0.7× 约 42%；medium 0.7–1.2× 约 25%；large >1.2× 约 8%；称 gap 大小是“最强的单一预测变量” — [tradingstats.net Gap Fill Indicator](https://tradingstats.net/gap-fill-indicator/)；[Gap Fill Strategy (NQ 2015–2025, 2,791 天)](https://tradingstats.net/gap-fill-strategy/)
- tiny gap + 首根 15 分钟 K 线确认方向，回补率 93.1%（773 例，似为 NQ）— [tradingstats.net Gap Fill Strategy](https://tradingstats.net/gap-fill-strategy/)

**C. 按开盘位置（区间内 vs 区间外）**
- 开在前日区间**内**的 gap 回补约 70%；开在前日区间**上方/下方**的 gap 回补约 43–47% — [tradingstats.net Gap Fill Indicator](https://tradingstats.net/gap-fill-indicator/)
- 12,390 个 NQ/ES/YM/RTY 交易日中，约 60% 开在前日区间内、25% gap up（开在前日高点上方）、15% gap down；该研究称 gap-up 与 gap-down 行为不对称（具体表格数字在摘要中被打乱，无法可靠引用）— [tradingstats.net Session Open Analysis](https://tradingstats.net/session-open-analysis-futures/)
- 单一作者样本：开盘在昨日 value area 内时，8 次 overnight gap 中 6 次在首小时回补，作者自称样本太小 — [Zipmex blog](https://zipmex.com/blog/s-p-overnight-gaps-filled-in-the-first-hour-6-of-8-times-inside-yesterdays-value-area-one-author-reports/)

**D. 回补时间分布（首小时）**
- ES：前 2.5 小时完成了 82.4% 的当日回补（NQ 86.1%）；开盘 15 分钟内（8:45 CT）ES 已回补 40.6%，NQ 接近一半；NQ 34% 在前 5 分钟回补；样本 ES 803 天、NQ 839 天 — [tradingstats.net When Do Gaps Fill](https://tradingstats.net/when-do-gaps-fill/)
- NQ（2015–2025，2,791 天）：首小时（9:30–10:30 ET）回补占全部 gap 的 43.3%，39.7% 当日从未回补 — [tradingstats.net Gap Fill Strategy](https://tradingstats.net/gap-fill-strategy/)
- 在“当日最终回补”的 ES 日子里，约一半回补发生在开盘半小时之后，但到 11:00 CT 已完成 82% 以上；gap 存活到 11:00 CT 后晚盘回补可能性显著下降 — [tradingstats.net When Do Gaps Fill](https://tradingstats.net/when-do-gaps-fill/)（据搜索摘要）
- NexusFi 文章称 0.25–0.5% 的 ES gap 首小时回补 48%，另称 >0.5% 的 gap 约 65% 在 RTH 首小时回补，但其自身分档数据与此矛盾，且无样本量/方法 — [NexusFi Academy: Fill the Gap](https://nexusfi.com/a/concepts/fill-the-gap)

**E. 方向、星期效应与近年数据**
- TradeThatSwing（Edgeful 数据，滚动 6 个月 SPY）：某时点 up 53% / down 59% 回补，另一时点 up 59% / down 69%；称随星期几变化明显（未给出可引用的分星期数字）；ES 0.05–0.2% 的 gap 上下两个方向都回补 88% — [TradeThatSwing SPY Gap Fill](https://tradethatswing.com/sp-500-spy-es-gap-fill-strategy-and-statistics/)；[TradeThatSwing ES Gap Fill](https://tradethatswing.com/gap-fill-strategy-on-es-or-mes/)
- SharePlanner（2018–2023）：SPY/QQQ 约 15–20% 的交易日 gap ≥1%；QQQ 1–2% 的 gap 当日完全回补约 45–47%；SPY gap up ≥1% 后开盘到收盘平均 -0.2%（仅 12 个最大 gap-up 日），QQQ -0.5%；QQQ 12 个最大 gap-down 日开盘到收盘平均 +0.1%；**SPY 周一 ≥1% gap-down 开盘后平均继续下跌约 0.20%**，与其他日子不同；周一大 gap-up 更易日内反转 — [SharePlanner: Fading the Gap](https://www.shareplanner.com/blog/strategies-for-trading/fading-the-gap-how-large-overnight-moves-in-spy-and-qqq-play-out-during-the-trading-day.html)（样本极小）
- Vortex Capital：2022 至 2026 年 5 月 6,552 个美股 gap 事件，>2% 的 gap 不延续，1–2% 的 up-gap 是唯一有真实优势的分档（53.7% 延续）— [Vortex Capital: The Gap Map](https://www.vortexcapitalgroup.com/insights/the-gap-map-when-us-equity-gaps-continue-fade-and-mean-nothing)（标的范围从摘要中不清楚）
- Strasmore 对 2026 上半年的分析：SPY 该半年最大的 gap 日开盘后仅变动 -0.08%——既不回补也不反转，只是形成新价位（单一案例，仅作示意）— [Strasmore: Why Do Stocks Gap Overnight](https://www.strasmore.com/blog/why-do-stocks-gap-overnight)

**F. Gap fade / gap-and-go 的交易回测**
- Kai Yasuda（2000–2026，单股，未扣滑点）：对 >2% 的指数 gap，**顺 gap 方向**交易 QQQ PF 1.50、SPY PF 1.15；QQQ 逆向 fade PF 0.65，275 笔中 39.6% 盈利；结论是 fade 在小 gap 上最多保本，gap 越大亏得越多 — [Kai Yasuda: The Gap-Fill Teardown](https://kaiyasuda.substack.com/p/the-gap-fill-teardown)
- QuantifiedStrategies 的 SPY gap-down 买入规则：gap down >0.15% 且 <0.6%，前日 IBS ≤0.25，前日 5 日 RSI 低（摘要写作 0.45，疑为笔误），开盘买入，收盘高于前收则平仓；目标设为 gap 的 0.75，每次回补平均 +0.19%；作者评价“不惊艳但尚可” — [QuantifiedStrategies Gap Trading](https://www.quantifiedstrategies.com/gap-trading-strategies/)
- 简单规则“SPY 开在前日低点下方即买入、持有至收阳”赚得远少于买入持有 — [Setup4Alpha](https://setup4alpha.substack.com/p/the-simplest-gap-down-reversal-trading)
- EasyLanguage Mastery：SPY 1993 年起的 gap fade PF 1.2，加过滤后 1.43（不同模型/时期，可能存在参数挖掘）— [EasyLanguage Mastery](https://easylanguagemastery.com/strategies/improve-simple-gap-strategy/)

**G. 学术研究**
- Plastun, Sibande, Gupta, Wohar（2020）：DJI、S&P 500、NASDAQ 1928–2018 日线，gap 日价格倾向于**沿 gap 方向**运动（动量），效应短暂；**没有证据表明 gap 在 5 日内被回补**，与“gap 总会回补”的流行观念相反；gap 无季节性 — [SSRN 3461283](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3461283)；[University of Pretoria repository PDF](https://repository.up.ac.za/server/api/core/bitstreams/f829a6c1-5762-48b1-89eb-a1ef54125843/content)（注意：其 gap 定义很可能是“当日最低价高于前日最高价”的 full gap，与 close-to-open gap 不同）
- 2025 年 JRFM 关于 DJIA/NASDAQ/DAX 周末 gap 的研究：命中率随距开盘价距离而变，认为不考虑微观结构、波动率状态和距离就无法直接利用周末 gap — [MDPI JRFM 18(3):132](https://www.mdpi.com/1911-8074/18/3/132)

### Inferences
- **与用户回测的对应**：用户的空头入场点（前收 = gap 回补点、前日低点、VA 边缘）恰好是“gap-down 回补路径”上的价位。gap-down 当日回补率（SPY 0.25–0.5% 档约 67%，2014 年后整体约 48%）意味着“反弹触及前收”本身是高概率事件，做空押注的是“回补后/回补前反转”，这一条件概率在找到的资料中**没有任何来源测量过**，用户的负 Sharpe 实际上就是对该条件概率的一次实测。
- 数据普遍显示 gap-down 比 gap-up 更容易回补（Kagels 各分档 down 比 up 高 3–7 个百分点；Edgeful 6 个月窗口 down 高 6–10 个百分点），即 gap-down 后的日内反弹（逆 gap 方向）比 gap-up 后的日内回落更“正常”。逆着这种反弹做空，结构上处于不利一侧。
- 2014 年后回补率下降 + 2022–2026 年大 gap“不延续也不回补”（Vortex、Strasmore）提示：近年开盘 gap 更像“新价位”而非“待修复的失衡”，以前收为磁铁的逻辑在用户的 2019–2026 样本期已弱化。
- **可编码、可回测的规则（基于以上统计）**：
  1. `gap_atr = (open - prev_close) / ATR14_daily`，分 4 档（<0.3、0.3–0.7、0.7–1.2、>1.2），再交叉 `open_location ∈ {inside_prev_VA, inside_prev_range_outside_VA, outside_prev_range}`，统计每格的当日回补率、回补时间分布、回补后 30/60 分钟的前进/回撤（MFE/MAE）。仅在 tiny/small 且区间内的格子里考虑“顺回补方向”交易（即 gap-down 时做多至前收），在 large 且区间外的格子里考虑顺 gap 方向。
  2. **时间衰减规则**：若到 10:00 / 10:30 / 11:00 ET 仍未回补，计算剩余时段的条件回补概率；若显著下降，则将“未回补 + 价格未回到开盘价上方”作为顺 gap 方向入场信号（与用户当前逆反弹做空相比，入场时点更晚但条件更强）。
  3. **首 15 分钟确认**：tradingstats 声称 tiny gap + 首根 15 分钟 K 线朝回补方向时回补 93.1%；可在 SPY 上复现：首 15 分钟收盘相对开盘的方向 × gap 档位 → 回补率。
  4. **分时期稳健性**：按 2001–2013 / 2014–2019 / 2020–2026 三段分别统计，任何规则须在后两段同向成立。
  5. **星期过滤**：单独检验周一 gap-down（SharePlanner 称周一 ≥1% gap-down 平均继续下跌 0.20%，样本小，需复核）。

### Gaps
- thetrading.tools 的 **down-gap 分档**当日回补率、按星期/年份的拆分未能获取（页面无法抓取）。
- 没有找到任何来源测量 **SPY 以 ATR 归一化**的 gap 回补率（ATR 分档数据仅来自 ES/NQ 期货的 tradingstats.net，且其方法无法核实）。
- 没有找到“gap 已回补（触及前收）之后”的价格行为统计（回补后继续 vs 反转的概率）——这恰恰是用户策略的核心条件，需要自行测算。
- 没有找到严格的“首小时未回补 → 当日剩余时段回补”条件概率（只有回补时间分布）。
- 2020 年之后（含 0DTE 爆发期）专门的 SPY gap 统计只有 Kagels 的 2014–2026 分段和若干滚动窗口快照，没有 2020–2026 的独立分段。
- 学术界关于“指数 close-to-open gap 当日回补”的同行评议研究几乎没有；Plastun 等研究的是日线 full gap，与日内交易问题不完全对应。

---

## 问题 2：Dalton 开盘类型的精确定义、15–30 分钟内的识别方法、对全天的含义，以及量化回测尝试

### Takeaway
Dalton 的四种开盘类型（OD / OTD / ORR / OA）在教育类资料中定义大体一致，但**都是定性描述，没有统一的量化阈值**；按“信心度”排序为 OD > OTD > ORR > OA。能找到的唯一透明的量化尝试（NexusFi 用户 MWG86，ES 2019–2020，455 个交易日）发现 OAIR 的趋势日比例（17.3%）反而略高于 Open Drive（16.4%），作者最终结论是“开盘类型/日类型没有历史优势”。所谓“OAIR = 80% 平衡日”“OAOR = 80% 趋势日”的说法无法溯源核实。

### Cited Findings

**A. 定义（来自 Dalton《Mind Over Markets》的二手摘要）**
- **Open Drive (OD)**：开盘后立即朝一个方向激进拍卖，**不再回到开盘价**；通常由开盘前已作出决定的 other-timeframe 参与者推动；信心度最高 — [LuxAlgo: Open Types](https://www.luxalgo.com/library/concept/open-types/)；[TPOCHART: Type of Opening](https://tpochart.com/education/type-of-opening-in-market-profile)
- **Open Test Drive (OTD)**：先朝一个方向测试某个已知参考位（前日高/低点、value area 边缘、POC），未能找到新业务/未获接受，随后反向驱动并穿越开盘价；这次失败的测试常常成为当日一个极值；信心度低于 OD — [LuxAlgo](https://www.luxalgo.com/library/concept/open-types/)；[Book review of *Markets in Profile*](https://whatheheckaboom.wordpress.com/2012/09/15/book-review-of-markets-in-profile-profiting-from-the-auction-process-by-james-dalton/)；有来源补充：OTD 允许打入 value 内部，但必须拒绝 POC，否则该开盘类型很可能在失败 — [tradingvolumeprofile blog](http://tradingvolumeprofile.blogspot.com/2018/03/opening-types.html)
- **Open Rejection Reverse (ORR)**：开盘后朝一个方向交易，遇到更强的反向力量，被推回并穿越开盘区间；与 OTD 类似，但初始运动更强、持续更久后才反转；方向信心低于 OD 和 OTD — [LuxAlgo](https://www.luxalgo.com/library/concept/open-types/)；[TrendDayTrading: Market Profile Trading](https://www.trenddaytrading.com/market-profile-trading)；有来源警告：教科书预期的“走到 value 另一端”在实践中并不总成立 — [Stratcos: Opening Types](https://stratcos.in/stacks/2020/08/08/understanding-market-profile-opening-types/)
- **Open Auction (OA)**：围绕开盘价上下轮动，无明确信念。**In range (OAIR)**：开在前日区间内 → 倾向接受、情绪未变、平衡/轮动日（normal / neutral / non-trend day）；**Out of range (OAOR)**：开在前日区间外 → 情绪可能改变，Dalton 书评称“通常导致任一方向的剧烈运动”；其他来源更谨慎，主张等 initial balance 完成再定方向 — [LuxAlgo](https://www.luxalgo.com/library/concept/open-types/)；[Book review](https://whatheheckaboom.wordpress.com/2012/09/15/book-review-of-markets-in-profile-profiting-from-the-auction-process-by-james-dalton/)；[MarketCalls: Open Type and Confidence](https://www.marketcalls.in/market-profile/market-profile-open-type-and-confidence.html)

**B. 开盘位置相对 value / range 的框架**
- 开在前日 value 内 → 平衡信号；若开在 value 内但首半小时无重叠交易就离开 value，可能是脱离平衡的 breakout；开在 value 外但在区间内 → 平衡程度较低但仍非强方向信号；开在区间外 → 较长周期参与者对前日 value 的拒绝，需等待确认（“no acceptance = no trade”）— [Scribd: Mind Over Markets 摘要](https://www.scribd.com/document/746366167/The-Mind-Over-the-Market)；[PureAlgo: Mind Over Markets](https://purealgocapital.com/1069-2/)；[ForexFactory AMT thread](https://www.forexfactory.com/thread/1301052-auction-market-theory-market-profile-trading)
- 若市场迅速回到前日 value area，则“很可能继续走到前日区间另一端”（即 80% rule 的变体）— [MarketCalls](https://www.marketcalls.in/market-profile/market-profile-open-type-and-confidence.html)

**C. 量化尝试**
- NexusFi 用户 MWG86，ES 2019–2020 共 455 个交易日（基于 volume profile 定义）：**OAIR 趋势日比例 17.3%，Open Drive 16.4%**，与 Market Profile 传统观点相反；开盘位置（区间内/外）并不能有效预测开盘类型（各类型出现概率大致相当）；前一日的日类型对当日几乎无预测力；作者最终写道“看不到使用日类型或开盘类型的任何历史优势”并停止更新 — [NexusFi Academy: Open Type Classification](https://nexusfi.com/a/concepts/open-type-classification)；原始讨论 [NexusFi thread: Searching for Day types and Opening types](https://nexusfi.com/showthread.php?t=56023)
- 同一 NexusFi Academy 站内其他页面称“OAIR = 80% 平衡/轮动日”“OAOR = 80% 趋势日”，归于“其他交易者的研究”，**无法溯源，且与上述 455 日研究矛盾** — [NexusFi Academy: Market Profile TPO Charts](https://nexusfi.com/a/market-structure/market-profile-tpo-charts)
- 趋势日基准率因定义不同差异很大：RTH 区间 >21 个 ES 点且收在极值 25% 以内 → 约 13–14% 的交易日 — [NexusFi Academy](https://nexusfi.com/a/concepts/open-type-classification)；Steidlmayer 式分类下趋势日 9.54%（Jan Firich 计算），且各日类型之间的相互关联未被证实 — [ATAS: Market Profile](https://atas.net/volume-analysis/basics-of-volume-analysis/how-to-improve-trading-using-the-market-profile/)；约 15–20% — [Breakingtrade](https://breakingtrade.com/blog/market-profile-day-types)
- 趋势日之后再出现趋势日的比例 13%，与 14% 的基准率无差异（“趋势日后市场会休息”的说法不成立）— [NexusFi Academy](https://nexusfi.com/a/concepts/open-type-classification)
- Noesis Analytics（卖指标的供应商）用开盘位置分类（HOR/HIR/NOR/LIR/LOR）统计约 1,337 个 ES 交易日：305 HOR、427 HIR、386 LIR、206 LOR、13 NOR；HIR 约 32%；HOR 日测试前日高点 68.9%，LOR 日测试前日高点 11.7%；至少一个 IB 边界被测试的比例 96.7–100%（与开盘类型无关）；同文另一处称 HIR+LIR 约 60%，两处数字需自行核对 — [Noesis: Market Profile Open Types](https://noesisanalytics.io/blog/market-profile-open-types)

### Inferences
- 用户回测中“触及前日价位 / VA 边缘无增益”与 MWG86 的 455 日 ES 研究方向一致：基于 value/range 位置的离散分类在 ES/SPY 上很可能只有很弱的预测力。开盘类型更适合作为**风险管理/仓位过滤**（例如避免在 OD 日逆势），而不是独立的入场 alpha。
- 用户的入场形态（gap-down → 反弹进入供给区 → 做空）在 Dalton 体系里对应“押注 OTD-down 或 ORR-down”（先向上测试参考位、失败后向下驱动）。但当反弹本身就是“gap-down 后的 Open Drive Up / 回补驱动”时，该空头等于逆 OD 交易——这正是 Dalton 体系中信心最低的做法。所以关键不是“价位”，而是**在入场前区分“测试失败”与“驱动/接受”**。
- **可编码的 1 分钟开盘类型分类器（建议参数，需网格稳健性测试，不是任何来源给出的阈值）**：
  - 定义 `O` = 9:30 开盘价，`ε` = 0.05×ATR14（日线）为“触及开盘价”的容差，`OR_n` = 首 n 分钟（n=5/15/30）高低点，参考位集合 `R` = {前收、前日高/低、前日 VAH/VAL/POC、盘前高/低}。
  - **OD**：前 30 分钟内价格从未回到 `O ± ε` 的反方向一侧，且离开 `O` 的距离 ≥ 0.25×ATR14。
  - **OTD**：前 15 分钟内先朝方向 A 触及某个 `R` 中的参考位（越过 ≤ ε 或接近 ≤ ε），随后在 30 分钟内反向穿越 `O` 并突破 `OR_15` 的另一侧，且此后不再回到首次测试的极值。
  - **ORR**：前 15–30 分钟朝方向 A 运动 ≥ 0.2×ATR14（无需触及参考位），随后反向穿越 `O` 并收在 `OR_30` 另一半。
  - **OA**：前 30 分钟穿越 `O` ≥ 3 次且 `OR_30` 宽度 < 0.35×ATR14；再按开盘位置拆为 OAIR / OAOR。
  - 输出变量：收盘相对 `O` 的方向/幅度、IB（首小时）单边/双边扩展、是否趋势日（收在全日区间 10–25% 极值内）、gap 是否回补、10:30 后 MFE/MAE。
- **建议的条件化测试**：开盘类型 × gap_atr 档位 × 开盘位置（value 内/区间内/区间外）三维交叉，检验 P(当日方向与驱动方向一致)。若 OD/OTD 在任一格子显著高于基准率，再把用户的空头规则限定在“OTD-down / OD-down after gap-down”的格子内；否则说明 Dalton 分类在 SPY 上也无 edge（与 MWG86 一致）。
- 由于 SPY/ES 趋势日基准率仅约 10–20%，任何“开盘类型预测趋势日”的规则都必须与基准率对比，否则容易把基准率误读为信号。

### Gaps
- 未找到 Dalton 原著对各开盘类型的**数值化阈值**（多少分钟、多大幅度）——原著本身就是定性的，二手资料也没有统一标准。
- 未找到任何同行评议或大样本（>1,000 日）的 SPY/ES 开盘类型回测；MWG86 只有 455 日且基于 volume profile 自定义规则，原始数据表未能获取。
- “OAIR 80% 平衡日 / OAOR 80% 趋势日”说法无法溯源。
- 未找到 OD/OTD/ORR/OA 各自在 ES/SPY 上的出现频率（Noesis 只给开盘位置分类的频率）。

---

## 问题 3：Gap-and-go vs gap-fade 规则、Opening Range（5/15/30 分钟）突破统计、Initial Balance（首小时）扩展统计

### Takeaway
ES 的首小时区间几乎总会被突破（无突破日仅约 0.6–2.2%），但“突破后能否延续”接近抛硬币，且加入事件顺序和交易成本后简单 ORB 在 ES 上净亏损。学术证据倾向于**日内动量**（前收到 10:00 的收益预测最后 30 分钟同向收益；SPY “noise area”突破动量策略样本内 Sharpe 1.33），但样本外明显衰减（一项复现 OOS Sharpe 0.39）。大 gap 顺势略优于逆势（SPY >2% gap 顺势 PF 1.15）。Dealer gamma 正值时日内倾向反转、负值时倾向动量，这可能是决定“gap-and-go vs gap-fade”的状态变量。

### Cited Findings

**A. Initial Balance（首小时）扩展**
- ES 2015–2025：约 52% 的交易日从 IB 高点向上扩展至少 25%（摘要措辞，可能指单侧）；18.8% 达到 100% 扩展；ES 扩展中位数为 IB 宽度的 63.6%；仅 2.2% 的 ES 交易日完全没有突破；窄 IB 日（占 ES 交易日 66.2%）突破率 98.7%，扩展中位数 74.8% — [tradingstats.net IB Breakout Statistics](https://tradingstats.net/initial-balance-breakout-statistics/)
- 另一组表述：仅 0.6% 的交易日完全收在 IB 内，双边突破约 40.1%（与上面的 2.2% 存在不一致，可能是不同口径）— [tradingstats.net IB Retest Statistics](https://tradingstats.net/initial-balance-retest-statistics/)（据搜索摘要）
- Team LBR（2008，ES 日盘自 2007-11-01）：IB 双边扩展 37%；**开在前日 VA 外时双边扩展 28%，开在 VA 内时 39%**（VA 子样本自 2008-04-10 起，较小）；IB 占全日区间的中位比例 48%，IB 为 NR7 时为 37% — [Team LBR: ES Initial Balance Stats](http://teamlbr.blogspot.com/2008/10/es-initial-balance-stats.html)
- TradingView 指标历史数据：IB 高点上方扩展的中位数 +0.31%，75 分位 +0.60%（数据集/时期不明）— [TradingView: Initial Balance Statistical Mapping](https://www.tradingview.com/script/2iuvi66N-Initial-Balance-Statistical-Mapping/)

**B. Opening Range Breakout（ORB）**
- Empirica Lab，ES 1,882 个交易日，5 分钟 OR：1,339 日（71%）在 10:00 前突破（683 向上 / 656 向下）；突破日中 42% 到收盘都未触及 OR 另一侧；88% 的突破能到达再延伸半个 OR 的位置，但**考虑事件顺序后，只有 39% 是在未先回到 OR 内的情况下到达**；单手 MES 的简单突破交易成本前 +$1,492，成本后 -$3,194 — [Empirica Lab: ORB on ES](https://empiricalab.substack.com/p/opening-range-breakout-es)
- ES 09:45–11:00 突破研究：12 个配置中 11 个直接亏损，所有配置样本外转负（“null result”）— [GitHub july-backtester PR #400](https://github.com/zachisit/july-backtester/pull/400)
- 15 分钟区间突破后，突破方向的平均走势在 3 小时后为负 — [Papers With Backtest: ORB](https://paperswithbacktest.com/strategies/opening-range-breakout)
- Zarattini & Aziz（SSRN 4416622）：QQQ 5 分钟 ORB，2016-01 至 2023-02，CAGR 33.2% vs 买入持有 14.9%，1,795 笔交易，假设零滑点、最高 4 倍杠杆、佣金 $0.0005/股 — [SSRN 4416622](https://papers.ssrn.com/abstract=4416622)；[CXO Advisory 摘要](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)；独立复现（NQ、SPX、Dow、DAX、FTSE 指数 CFD）：毛收益可复现，**扣成本后为零** — [MQL5 blog replication](https://www.mql5.com/en/blogs/post/776235)
- Edgeful 的 ORB 宣传文（如“6 个月 108% 收益”）为营销性质、方法不透明 — [Edgeful blog](https://www.edgeful.com/blog/posts/5-minute-opening-range-breakout-es-strategy)

**C. 日内动量（学术）**
- Gao, Han, Li, Zhou：SPY 1993–2013，**前收到首个半小时结束（约 10:00）的收益**正向预测最后半小时收益；在高波动、高成交量、衰退期、重大宏观数据发布日更强 — [SSRN 2440866: Market Intraday Momentum](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)；二手摘要报告回归斜率 0.069（显著）、简单策略年化 6.34% — [Alpha Architect](https://alphaarchitect.com/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- Baltussen 等将该模式扩展到 60 余个期货市场（1974–2020），据二手摘要 — [Quantum Bias 综述](https://quantum-bias.com/blog/first-last-half-hour-intraday-momentum)
- Zarattini, Aziz, Barbon “Beat the Market”：SPY，以“过去 14 天同一时刻相对开盘价的平均绝对偏离”构造 noise area 上下轨，突破即顺势；2007–2024 年初净收益 1,985%、年化 19.6%、Sharpe 1.33（SPY 买入持有 0.45）— [Concretum Group](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)；[Univ. St. Gallen repository](https://alexandria.unisg.ch/entities/publication/71ef0a23-34e3-4b37-a8d7-d98285579662)
- 独立复现：样本内 Sharpe 1.34（年化 19.8%），**样本外 Sharpe 降至 0.39，跑输 SPY 买入持有** — [Larry Swedroe Substack](https://larryswedroe.substack.com/p/when-beat-the-market-meets-the-real)；[GitHub: PazSheimy OOS replication](https://github.com/PazSheimy/spy-intraday-momentum-oos)；Nasdaq-100 期货重建：多头样本内外均为正但 Sharpe 较低，空头表现差（“short is a mirage”）— [EdgeLab Trading](https://edgelabtrading.com/blog/zarattini-intraday-momentum-nasdaq/)

**D. 2020 年后结构变化：0DTE 与 dealer gamma**
- Dim, Eraker, Vilkov：做市商库存 gamma 为正时**日内反转增强**，为负时**动量增强**；后续版本（样本延至 2026 年 2 月）表述为负（正）事前 gamma 失衡与流动性不足的交互解释日内动量（反转）— [SSRN 4692190: 0DTEs: Trading, Gamma Risk and Volatility Propagation](https://papers.ssrn.com/sol3/Delivery.cfm/4692190.pdf?abstractid=4692190&mirid=1)；[ResearchGate](https://www.researchgate.net/publication/377984312_0DTEs_Trading_Gamma_Risk_and_Volatility_Propagation)
- Adams, Fontaine, Ornthanalai：0DTE 交易与 S&P 500 实现波动率呈稳健负相关；额外对冲需求主要来自滚入 0DTE 状态的长期限期权存量 — [Adams et al. PDF](https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf)；[Quantpedia 摘要](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)
- Cboe 估计 2023 年做市商 0DTE 净 gamma 仅占 S&P 500 期货日流动性的 0.04%–0.17%（二手转述）— [Quantpedia](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)
- 普林斯顿论文：0DTE 交易与日内波动相关，但证据不支持“gamma 对冲反馈”作为主要机制 — [Princeton Thesis Central](https://theses-dissertations.princeton.edu/entities/publication/61115cd1-cb09-4a8b-9230-ff488fc2a386)

### Inferences
- **为什么“fade rally”失败的一个解释**：日内动量文献（Gao 等；Zarattini 等）说明 SPY 日内收益存在正自相关，而 gap-down 后的上涨反弹若突破 noise area 上轨，即属于“动量”信号——用户在该点做空等于站在动量的对立面。用户若要保留“gap-down 后做空”的思路，应改为**等待反弹失败（价格重新跌破开盘价/VWAP 或跌出 noise area 下轨）后顺势**，而不是在反弹中途逆势。
- ORB/IB 统计显示“突破必然发生、延续接近随机”：IB 几乎 100% 被至少一侧突破，所以“触及前日价位/VA 边缘”这类事件也几乎每天发生，缺乏选择性——与用户“触及价位不增加 edge”的发现一致。
- Team LBR 的 28% vs 39% 说明：**开在 VA 外的日子更倾向单边**（双边扩展更少），因此 gap 开在前日 VA/区间外时，逆向 fade 更危险；这与 tradingstats“区间外 gap 回补率仅 43–47%”方向一致。
- 0DTE/gamma 文献提示一个可能比“价位”更有用的状态变量：**dealer gamma 正 → 均值回归（fade 有利），gamma 负 → 动量（go 有利）**。用户的 0DTE put 策略收益可能随 gamma 状态大幅变化，聚合后变成 ≈0 Sharpe。
- **可编码规则**：
  1. **Noise-area 过滤**：按 Zarattini 定义计算每分钟上下轨（过去 14 日同一时刻 |close_t/open - 1| 的均值，以 max(open, prev_close) / min(open, prev_close) 为锚）；只在价格位于 noise area 内时允许 fade，价格突破上轨时禁止做空（或改为做多），突破下轨时顺势做空。
  2. **Gao 动量偏置**：`r_bias = close_10:00 / prev_close - 1`；若 gap-down 但 `r_bias > 0`（已收复 gap），禁止当日做空；检验最后 30 分钟方向与 `r_bias` 同号的比例及其 2020 年后是否衰减。
  3. **IB 规则**：首小时结束时计算 `IB_width / avg_IB_width_20d`；窄 IB（<0.8）的突破方向顺势、宽 IB（>1.2）时 fade IB 边缘；交叉开盘位置（VA 内/外）检验双边扩展概率是否复现 39% vs 28%。
  4. **ORB 事件顺序**：所有 ORB/IB 目标命中率必须按“先触及目标还是先触及止损/OR 另一侧”的路径顺序计算（Empirica 的 88% → 39% 是典型陷阱）。
  5. **Gamma 状态分层**：若有 SPX 期权持仓数据（或用 VIX1D/VIX 比率、前日实现波动等代理），把所有上述规则按正/负 gamma 分层回测。
  6. **大 gap 顺势**：|gap| > 1.2×ATR（或 >1–2%）时只做顺 gap 方向，检验 SPY 能否复现 Yasuda 的 PF 1.15（扣成本后）。

### Gaps
- 未找到 SPY（而非 ES/NQ）的 IB 扩展大样本统计；tradingstats 的两组 IB 数字口径不一致且无法抓取全文核对。
- 未找到“gap-and-go vs gap-fade”在 SPY 上按 ATR 和开盘位置交叉的完整回测；Vortex 的 6,552 事件样本标的范围不明。
- Gao 等论文的样本止于 2013 年，未找到 2020 年后 SPY 首半小时→末半小时效应的独立更新；Dim 等论文的具体系数未能读取全文。
- 未找到 0DTE 时代（2022 年后）开盘类型或 gap 回补率随 gamma 状态变化的直接统计。

---

## 问题 4：80% rule（value area）及类似拍卖理论规则——宣称成功率 vs 实测成功率

### Takeaway
80% rule（开在前日 VA 外、重新进入并在 VA 内停留两个连续 30 分钟 TPO 时段 → 约 80% 概率穿越整个 VA）**没有找到任何透明、可复现的 ES/SPY 回测**；其起源是 1987–1991 年 Dalton Capital 的 Profile Reports 中的经验法则。网上的“67–68% 胜率”无测试者和方法；交易者论坛中的自测结果约为 40% 多到略高于 50%，且该形态出现频率低。触发条件的定义在不同来源间不一致，使得任何数字都难以比较。

### Cited Findings
- 规则内容：前一交易日 value area（约 70% 成交量/TPO）之外开盘，重新进入 VA 并在 VA 内停留连续两个 30 分钟时段，则约 80% 概率走到 VA 另一端 — [QuantVPS: Value Area Trading Strategy](https://www.quantvps.com/blog/value-area-trading-strategy-guide)；[PipSafe: The 80% Value Area Rule](https://www.pipsafe.com/the-value-area-80-rule/)
- 起源与地位：通常追溯至 Dalton Capital 1987–1991 年的 Profile Reports；“80%”是经验标签而非严格审计的统计量，实际成功率随市场与时代变化 — [LuxAlgo: 80% Rule](https://www.luxalgo.com/library/concept/80-percent-rule/)
- QuantVPS 明确建议把 80% 当作该文献中的 rule of thumb，**而非经过测试的统计量** — [QuantVPS](https://www.quantvps.com/blog/value-area-trading-strategy-guide)
- 定义分歧：Shadowtrader 称两个 30 分钟时段都不需要收在 value 内，第一个时段收在 value 内即可开始计数；其他来源要求连续两个时段收回 VA 内 — [Shadowtrader Glossary](https://www.shadowtrader.net/glossary/eighty-percent-rule/)；[QuantVPS](https://www.quantvps.com/blog/value-area-trading-strategy-guide)
- 乐观宣称：“独立测试准确率 67%”、“ES 期货历史胜率 68%、平均盈亏比 1.5:1”——未给出测试者、样本或方法 — [TradeAlgo](https://www.tradealgo.com/trading-guides/technical-analysis/market-profile-how-to-understand-value-areas-and-price-distribution)
- 怀疑性实测：一位交易者在 X 上称该情形在 ES 上发生的统计“略高于 40%” — [X / @Am_Shai](https://twitter.com/Am_Shai/status/1680924992421396481)；NexusFi 论坛评论称胜率“仅略高于 50%”，称 80% rule 是神话，且该形态较少出现 — [NexusFi thread #30847](https://nexusfi.com/showthread.php?t=30847)
- FTMO、JournalPlus 等页面只是重复 80% 前提，无测试数据 — [FTMO blog](https://ftmo.com/en/blog/market-profile-master-the-80-trading-strategy-hidden-magnets/)；[JournalPlus](https://journalplus.co/strategies/market-profile-strategy/)
- 相关的“回到 value 即走到另一端”说法也只是定性描述 — [MarketCalls](https://www.marketcalls.in/market-profile/market-profile-open-type-and-confidence.html)
- 其他拍卖理论规则的实测：MWG86 的 455 日 ES 研究认为开盘类型/日类型无历史优势 — [NexusFi Academy](https://nexusfi.com/a/concepts/open-type-classification)；ATAS 引用 Jan Firich 的计算称各日类型之间的关联未被证实 — [ATAS](https://atas.net/volume-analysis/basics-of-volume-analysis/how-to-improve-trading-using-the-market-profile/)

### Inferences
- 用户发现“value area 边缘无 edge”与可找到的实测证据一致：拍卖理论中最著名的量化规则（80% rule）在公开实测中只有约 40–55% 的成功率，且没有人展示过扣成本后的盈利。
- 80% rule 的成功率必须与**无条件基准**比较：ES/SPY 每天触及前日 VA 两端中至少一端的比例本身就很高（IB 几乎每天被突破，Noesis 显示 IB 边界被测试 96.7–100%），因此“穿越 VA”的条件概率若仅略高于基准，就没有信息量。
- **可编码规则（精确版 80% rule 测试）**：
  1. 前日 VA：用 1 分钟 SPY 数据按成交量分布（价格分箱 = 0.05 美元或 0.01×ATR）计算 70% value area 的 VAH/VAL/POC；另做 TPO 版（30 分钟分段）对照。
  2. 条件：开盘价在 VA 外（分“VA 外但前日区间内”和“前日区间外”两组）；之后价格进入 VA；变体 A = 连续两个 30 分钟 bracket 的收盘都在 VA 内；变体 B = 两个 bracket 都有成交在 VA 内（Shadowtrader 版）；变体 C = 仅第一次进入。
  3. 结果：当日收盘前是否触及 VA 另一端；触及前的最大不利偏离（MAE）；入场 = 第二个 bracket 收盘，止损 = 重新离开 VA 的一侧，目标 = 对侧 VA 边缘。
  4. 基准：同一天、同一时刻随机入场（同方向）到达同一目标的概率；按 2019–2021 / 2022–2026（0DTE 时代）分段。
  5. 与用户的 gap-down 场景关联：gap-down 开在前日 VA 下方后重新进入 VA 并停留两个 bracket，80% rule 预测是**向上**穿越至 VAH——这与用户在 VA 做空的方向**相反**；可直接检验“用户空头信号与 80% rule 触发同时出现”的子样本是否贡献了主要亏损。

### Gaps
- 未找到任何公开、透明、含样本期和成本的 80% rule ES/SPY 回测；“40% 多”“略高于 50%”“67–68%”均无法核实方法。
- 未找到 Dalton 原始 Profile Reports 中 80% 数字的计算方法与样本。
- 未找到其他拍卖理论规则（如 “poor high/low 会被重访”、“single prints 会被回补”、“naked POC 会被测试”）在 SPY/ES 上的可靠实测统计（本次未专门搜索，仅在 NexusFi Academy 目录中看到相关定性条目）。

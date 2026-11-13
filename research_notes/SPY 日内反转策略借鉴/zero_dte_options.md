# 0DTE 期权对标普 500 日内动态的影响，以及日内买入 0DTE put 的经济性

> 研究背景：策略在缺口低开 + 反弹失败后的第一小时买入 SPY 0DTE put（或做空 SPY），标的回测（2019-2026）显示近乎零 edge。本笔记回答两件事：(a) 0DTE 热潮（SPX 自 2022-05 起每日到期，SPY 自 2022-11 起每日到期）是否改变了开盘时段的行为（均值回归 vs 趋势、波动被抑制还是放大）；(b) 日内买入 0DTE put 的期权层面成本/优势。
>
> 方法说明：本次沙箱内 WebFetch 对 papers.ssrn.com、cdn.cboe.com、www.sec.gov、carey.jhu.edu、jean-sebastienfontaine.com、quantpedia.com、concretumgroup.substack.com 均无法解析（网络 allowlist 限制），只有 github.com 成功抓取了原文（Vilkov 的 0DTE Trading Rules 复现包）。因此大部分论文结论来自 WebSearch 返回的摘要/二手概述，引用处已注明；凡数字不一致之处均已标出。"同行评审"与"工作论文/厂商宣传"已分别标注。

---

## 问题一：学术/官方研究——0DTE 交易让日内波动变大还是变小？何时放大？

### Takeaway
主流证据（多数为工作论文，尚非期刊定稿）倾向于"0DTE 平均而言并未放大、甚至略微抑制了 S&P 500 日内波动"：做市商（MM）在 0DTE 上的净 gamma 通常为正，正 gamma 时期日内**反转增强**、负 gamma 时期**动量增强**；唯一主要反对声音是 Brogaard, Han & Won（0DTE 交易量 +1σ → 波动 +9.1%），但其结论受到复现质疑。对你的策略而言，关键不是"0DTE 有没有改变平均行为"，而是"当天处于正 gamma 还是负 gamma 状态"。

### Cited Findings

**时间线与规模（用于划分回测 regime）**
- SPXW 周二、周四到期分别于 2022-04-18 和 2022-05-11 加入，自此 SPX 每个交易日都有 0DTE — [Vilkov, 0DTE Trading Rules 复现包（GitHub 原文）](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- SPY 与 QQQ 的周二到期 weeklys 计划于 2022-11-14 上市、周四到期于 2022-11-16 上市（首个到期日为 2022-11-15 / 11-17）；IWM 未纳入 — [Cboe 产品更新通告](https://cdn.cboe.com/resources/product_update/2022/Update-Cboe-Options-to-List-SPY-and-QQQ-Tuesday-and-Thursday-Expiring-Weekly-Options.pdf)；[MIAX Regulatory Alert 2022-11-14](https://miaxglobal.com/alert/2022/11/14/miax-exchange-group-options-markets-listing-tuesday-and-thursday-weekly-1)
- 2025 全年 SPX 0DTE 日均成交 230 万张，占 SPX 总成交 59%（创纪录） — [Cboe 2025 年度成交量公告](https://ir.cboe.com/news/news-details/2026/Cboe-Global-Markets-Reports-Trading-Volume-for-December-and-Full-Year-2025/default.aspx)；单月最高为 2025 年 8 月的 62.4% — [Cboe Insights](https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-record-62-share-in-august)；有聚合站称 2016 年该比例约 5%（二手，未核实） — [walnutinvest](https://walnutinvest.com/stats/options-trading-statistics)

**认为 0DTE 抑制波动/不传播波动的研究**
- Dim, Eraker & Vilkov,《0DTEs: Trading, Gamma Risk and Volatility Propagation》（SSRN 4692190，工作论文，2023 年底首发）：MM 在 0DTE 上的库存净 gamma 平均为正，且与未来日内波动负相关；**正的 MM 库存 gamma 增强日内价格反转，负 gamma 增强动量**；结果与 delta 对冲一致、与信息交易不一致；未发现 0DTE 未平仓 gamma 传播或无条件提高指数波动的证据 — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190)；[ResearchGate](https://www.researchgate.net/publication/377984312_0DTEs_Trading_Gamma_Risk_and_Volatility_Propagation)（均为搜索摘要，未读全文）
- 同一论文：0DTE 成交量正向冲击伴随并领先标的成交量上升；后期样本中标的收益对 0DTE 成交量冲击反应更强，但作者称差异"经济上可忽略"；0DTE 是各期限中 volatility risk premium 最大的 — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190)（搜索摘要）
- Adams, Fontaine & Ornthanalai,《The Market for 0DTE: The Role of Liquidity Providers in Volatility Attenuation》（SSRN 4881008，工作论文）：MM 对 SPX 0DTE 的中介使指数波动平均下降，有 0DTE 交易的日子指数波动降低 60–90 个年化基点；机制是到期头寸的对冲在指数期货上产生相互抵消的日内订单流 — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4881008)（搜索摘要）
- Adams, Dim, Eraker, Fontaine, Ornthanalai & Vilkov,《Do S&P500 Options Increase Market Volatility? Evidence from 0DTEs》（SSRN 5641974，工作论文）：0DTE 到期日的 10 分钟已实现波动更低；MM 在这些日子持有更大的正净 gamma；**抑制效应主要来自"长期限头寸滚入到期日"而非当日新开的 0DTE 交易**；日内对冲需求变化预测更强的订单流反转、更弱的动量 — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5641974)；[Quantpedia 摘要](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)（二手）
- Cboe 自家研究（厂商/交易所，非同行评审）：《Much Ado About 0DTEs》称 SPX 0DTE 的 MM 净 gamma 敞口日内在 $170mm–$670mm 之间，"相当可忽略"，未观察到破坏性市场冲击，SPX 日内波动与价格形态与历史均值一致 — [Cboe Insights](https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options)；2025 年的"0DTEs Decoded"报告据二手概述称客户 0DTE 买卖接近平衡，MM 净 gamma 对冲仅约占 SPX 日流动性 0.2%（另一概述给出 0.04%–0.17% 的 S&P 期货流动性，两数不一致） — [Interactive Brokers Campus 转载/概述](https://www.interactivebrokers.com/campus/traders-insight/securities/options/much-ado-about-0dtes-separating-fact-from-fiction/)
- 一篇托管在 Cboe 网站的论文《0DTE Index Options and Market Volatility: How Large is Their Impact?》（样本 2020-07 至 2023-06）估计 OMM gamma 对年化日波动的**最大**推升约 3.3 个百分点 — [Cboe PDF](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)（搜索摘要；作者未能确认）
- BIS 的一个专栏（box）检验了"0DTE 兴起是否把交易从一个月期权中抽走、从而压低 VIX"，结论是净效应上没有；并提到 0DTE 便宜、具有彩票式收益，以及类似机制在 2018-02 "Volmageddon" 前可能也存在 — [BIS: What could explain the recent drop in the VIX?](https://www.bis.org/publications/what-could-explain-recent-drop-vix)（具体期次与作者未能确认）

**认为 0DTE 放大波动的研究**
- Brogaard, Han & Won（SSRN 4426358；早期题目"How does zero-day-to-expiry options trading affect the volatility of underlying assets?"，后改为"Does 0DTE Options Trading Increase Volatility?"，2026 年 1 月修订）：以指数周期权分批上市为工具变量，0DTE 交易量 +1 个标准差 → 波动相对均值 +9.10%；控制 MM gamma 对冲后影响仍为正，主要由投机性散户驱动 — [ResearchGate](https://www.researchgate.net/publication/414775201_Does_0DTE_Options_Trading_Increase_Volatility)（搜索摘要）
- 一篇博客（非同行评审）用 1,083 个 SPX 交易日复测该 +9% 结论，称只测得约 0.6% — [DEV Community / FirmTape](https://dev.to/firmtape/does-0dte-options-trading-raise-volatility-a-published-9-claim-measures-06-on-1083-spx-nni)
- 一篇普林斯顿本科论文（非同行评审）认为 0DTE 交易与日内波动相关，但经典的"对冲反馈渠道"对日内方差预测没有显著增量预测力 — [Princeton Thesis Central](https://theses-dissertations.princeton.edu/entities/publication/61115cd1-cb09-4a8b-9230-ff488fc2a386)

**前 0DTE 时代的背景（机制同源）**
- Baltussen, Da, Lammers & Martens（*Journal of Financial Economics* 2021，同行评审）：S&P 500 市场日内动量（当日早前收益预测最后半小时收益）与期权做市商 gamma 对冲相关；MM 净 gamma 为负时动量最强，净 gamma 为正时基本消失 — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598)；[工作论文 PDF](https://twoquants.com/wp-content/uploads/2021/02/2020_Baltussen_LAmmers_Martens_Intra-day-Momentum.pdf)

**开盘时段**
- Božović（SSRN 5223127，工作论文）：标的指数日内跳跃频繁且影响大，跳跃强度在**开盘与收盘附近聚集**；SPXW 0DTE 中隐含的跳跃风险溢价很大 — [SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/5223127.pdf?abstractid=5223127&mirid=1)（搜索摘要）
- Vilkov 对 2022 年结构断点（前期截至 2022-04-14，后期自 2022-05-11）的检验显示 0DTE 策略表现的变化"统计上很弱" — [GitHub 原文](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)

### Inferences
- 学术主流（Dim/Eraker/Vilkov；Adams 等两篇）与 Cboe 的结论方向一致：**0DTE 时代的平均日内环境更偏"正 gamma → 均值回归/波动抑制"**。这对"缺口低开 → 反弹失败 → 继续下跌"这类**顺势延续**型交易是逆风：在正 gamma 日，开盘后的回补反弹更可能成功（反转），put 更可能亏损。
- 但这些效应是条件性的：负 gamma 日（例如大幅跳空低开、价格跌破大量 put 持仓所在行权价、VIX 走高）恰好是动量被增强的环境（Dim 等；Baltussen 等）。你的回测"整体零 edge"可能掩盖了**正 gamma 日为负 edge、负 gamma 日为正 edge**的相互抵消，这是最值得做的拆分。
- Adams 等指出抑制效应主要来自**长期限期权滚入到期日**，而非当日 0DTE 交易本身——这意味着"0DTE 成交量占比"并不是好的 regime 指标，真正相关的是 MM 在所有临近到期合约上的净 gamma。
- 2022-05（SPX）与 2022-11（SPY）是两个自然断点；你的 2019-2026 样本可以用 2019-01 至 2022-04、2022-05 至 2022-11、2022-11 以后三段做对比。不过 Vilkov 的断点检验很弱、Cboe 称日内形态与历史一致，所以**不应预期看到显著的结构性变化**；更可能的差异在 gamma 状态维度而非时间维度。
- 开盘附近跳跃风险最集中（Božović），意味着第一小时的 0DTE 期权价格里包含相对多的跳跃溢价——买方在开盘时段是在"贵的时候买"。

### Gaps
- 未找到专门研究"0DTE 引入前后**第一小时**/缺口日行为（缺口回补率、首小时自相关）"的学术论文；Baltussen 等聚焦最后半小时。需要用自有数据检验。
- 未找到 2023 年 BIS Quarterly Review 中专门讨论 0DTE / "mini-Volmageddon" 的文章原文，只确认了一个关于 VIX 下跌的 BIS box；未找到相关的美联储（Fed）note。JPMorgan（Kolanovic）"Volmageddon 2.0"警告的原始出处也未检索到。
- 所有 SSRN 论文均未能读取全文（网络限制），样本期、具体系数、是否区分时段等细节需在 SSRN 放行后核对。"0DTE Index Options and Market Volatility" 一文的作者未确认。

---

## 问题二：买入 0DTE 期权的回报与成本（含散户证据、VRP、put vs call）

### Takeaway
0DTE 期权平均而言定价偏贵（正的 variance risk premium，且 0DTE 是所有期限中 VRP 最大的），持有至到期的 OTM put 平均收益显著为负、中位数为 -100%；散户 0DTE 单腿买方整体亏损（不同版本估计每日亏损 $18.4 万至 $35.8 万），但亏损幅度对"如何识别散户"高度敏感。不过 Vilkov 的原文数据显示，以标的价格计的 VRP **绝对值很小**——对于 30-90 分钟持有的方向性买方，主要的结构性成本是买卖价差和 IV 变动，而非 VRP 本身。

### Cited Findings

**0DTE 期权收益（持有至到期）**
- Almeida, Freire & Hizmeri,《0DTE Asset Pricing》（工作论文）：0DTE 期权平均收益普遍为负；OTM put 平均收益始终为负且统计显著；**所有 OTM put 的中位收益都等于 -100%**；OTM call 平均收益比 OTM put 更负，且随行权价升高而下降；裸卖 OTM call 通常盈利；更长期限的 OTM call 平均收益没那么负 — [FMA 2025 Derivatives 会议论文 PDF](https://www.fma.org/assets/docs/Derivatives2025/Almeida.pdf)（搜索摘要）
- 有二手概述称该文发现约 70% 的 0DTE 违反随机占优价格界限，0DTE 投资者主要为上行波动获得补偿 — [FirmTape: What the 0DTE literature actually claims](https://firmtape.com/research/what-the-0dte-literature-claims)（二手，未核实）
- Vilkov,《0DTE Trading Rules: Tail Risk, Implementation, and Tactical Timing》（工作论文，GitHub 复现包原文，样本 SPXW 0DTE 2016-09 至 2026-01，10:00 ET 建仓持有至 16:00）：收益波动极大（OTM 尤甚），均值常常与 0 无显著差异；**ATM 至 OTM 的 call 和大多数 put 平均亏损**（以 PNL/现货计）；卖出略 OTM 的 call 和 put 在最多 75% 的观测中盈利 — [GitHub 原文](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- 同文：全样本 0DTE VRP 为正且显著，但**经济量级小**——即使在"已实现方差为零"的极端情形，溢价也只约为现货的 0.20%；10:00 ET 至到期的已实现 VRP 中位数约为标的的 0.0011% — [GitHub 原文](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- 同文的交易成本模型：每腿半个报价价差 + 0.5bp 滑点与费用；从中间价改为 bid/ask 成交后多数策略均值 PNL 与 Sharpe 下降。样本外（expanding window）择时策略的 gross → net Sharpe：put ratio spread 1.18 → 0.93；strangle/straddle 0.56 → 0.39；iron butterfly/condor 0.77 → **−0.20**；所有策略组合 0.81 → 0.25 — [GitHub 原文](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- 同文尾部风险：日度 net-PNL 的 ES1% 约为标的的 0.58%–1.58%；即便均值为正的策略，最差日与累计回撤也很严重 — [GitHub 原文](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- Bandi, Fusari & Renò,《0DTE Option Pricing》（SSRN 4503344，工作论文，日内数据 2014-01-02 至 2023-05-11）：基于对数收益特征函数的 Edgeworth 型展开给出偏度/峰度修正，显著改善 0DTE 定价与对冲；通过结构化估计 0DTE 隐含的收益与方差风险溢价，给出"近乎即时的可预测性"的提示性证据（未见具体策略回测） — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4503344)；[ResearchGate](https://www.researchgate.net/publication/372407812_0DTE_Option_Pricing)（搜索摘要）
- OptionMetrics（数据商博客，非同行评审）：在 399 个周五到期日上，SPX 和大盘单股 0DTE 在开盘时的隐含方差通常高于预测的已实现方差（VRP 均值与中位数均为正），但**在已实现波动偏高的一天之后，这一差距有时会反转** — [OptionMetrics](https://optionmetrics.com/blog/the-0-dte-variance-premium-mag7-reward-more-and-punish-harder/)

**散户 0DTE 损益与价差成本（争议较大）**
- Beckmeyer, Branger & Gayda,《Retail Traders Love 0DTE Options... But Should They?》（SSRN 4404704，工作论文）：用 Cboe 散户价格改善机制识别散户订单。不同版本/二手来源数字不一：早期版本（2021-02 至 2023-02）0DTE 每日亏损约 $18.4 万；后期版本（2021-02 至 2023-09）平均每日亏损约 $24.1 万，2022-05 SPX 每日到期后升至约 $35 万（另一来源为 $35.8 万）；超过 75% 的散户 SPX 期权交易为 0DTE；亏损集中在**单腿、付权利金（买方）、高 IV** 的交易，多腿交易显著更好但平均仍亏 — [ResearchGate](https://www.researchgate.net/publication/370012499_Retail_Traders_Love_0DTE_Options_But_Should_They)；[作者推文](https://twitter.com/beckmeyerheiner/status/1642068464859848704)（数字来自搜索摘要的二手汇总）
- Cboe 的反驳（交易所研究，利益相关）：2024 年 Cboe 论文称 Beckmeyer 等高估了散户单腿 SPX 0DTE 占比，至 2024Q1 复杂策略仍占散户 SPX 0DTE 成交多数 — [Cboe PDF](https://cdn.cboe.com/resources/government_relations/Understanding-Retail-Investors-Dynamic-Trading-Behavior-in-the-US-Options-Market_2024.pdf)；Amaya, Garcia-Ares, Pearson & Vasquez（2025-04 工作论文，Cboe Options Institute 资助）用记录真实方向的 Cboe 数据、按持有至到期计算，Cboe 客户单腿 auction 交易平均盈利（约每日 $34 万，但 t 值仅 0.29，不显著），并指出 auction 代理变量只覆盖 SPX 期权交易的 4%–6% — [Cboe PDF](https://cdn.cboe.com/resources/education/research_publications/Retail_Profitability.pdf)（搜索摘要）
- Bogousslavsky & Muravyev,《An Anatomy of Retail Option Trading》（工作论文；5,182 名交易者、240 万笔母单、约 $150 亿交易，2020-2022）：0DTE 期权交易相对其他期权交易多亏 4.71%（t = −10.09；另一稿约 3%）；尽管买卖价差很宽（典型期权价差 5%–10% 以上），散户期权交易实际亏损远小于价差，作者认为散户使用限价单规避了部分价差 — [LSU 会议版 PDF](https://www.lsu.edu/business/files/event-files/2025-finance-mardi-gras/retail_option_trading_v2.pdf)
- Bryzgalova, Pavlova & Sikorskaya（2019-11 至 2021-06 全市场数据）：散户偏好便宜的周期权，其平均买卖价差高达 12.6% — 见搜索返回的二手汇总 [rorlabs](https://rorlabs.io/options-futures-trading-money-loss-risk/)（二手，未读原文）
- SEC DERA 有一篇《Hope at a Reasonable Price: Customer Use of Limit Orders in the 0DTE Market》（2025-03）专门研究 0DTE 客户限价单 — [SEC PDF](https://www.sec.gov/files/dera-hope-reasonable-prc-2503.pdf)（仅确认存在，内容未能读取）

**厂商/数据站统计（非同行评审，方法不透明）**
- Option Alpha（23 万笔 0DTE 交易）：iron butterfly / iron condor 占 78% 仓位，胜率 66.76% / 70.19%；持续盈利者大约在 10:15 ET 建仓、12:00 后不久平仓；整体成功率约 50% — [Option Alpha](https://optionalpha.com/blog/0dte-options-strategy-performance)
- iPresage（所有标的，非仅 0DTE）：临近到期的买方期权平均每笔 −11.3%，胜率 37.2%，盈利交易平均 +89.7% — [iPresage](https://www.ipresage.com/research/optimal-dte-study)
- Options Cafe 的 SPY 0DTE 开盘区间突破回测：胜率 41.25%，盈利单约为亏损单的 2 倍；put 胜率 42.19% 略高于 call 的 40.57% — [Options Cafe](https://options.cafe/blog/0dte-opening-range-breakout-strategy-spy-backtested-results/)
- OptionKrafter：10:00 建仓的 0DTE iron condor 在 602 笔中胜率 75.4% 但仍亏钱（平均亏损约 $69，约为平均盈利 $21 的 3 倍） — [OptionKrafter](https://optionkrafter.com/blog/0dte-iron-condor)

### Inferences
- **持有到期 vs 30-90 分钟持有要分开看。** 学术文献中"OTM put 中位数 −100%"是持有至收盘的结果；你的交易只持有 30-90 分钟，承担的只是 VRP 与 theta 的一小段。Vilkov 的数据显示即便全日 VRP 也只约为现货的 0.0011%（中位数）到 0.20%（极端上限），按比例分到 1 小时更小——所以**对短持有的方向性买方，VRP 不是主要成本**。
- 理论上，如果隐含波动 = 已实现波动（无 VRP），long ATM 期权的 theta 损失会被 gamma 收益在期望上补偿；真正的结构性"漏损"= 买卖价差 + VRP 分摊 + 开盘 IV 回落（vega）。因此在标的方向 edge 为零的情况下，**期权不会创造 edge，只会把"零 edge"变成"略负 edge"**，代价换来的是凸性（亏损有上限、尾部收益放大）。
- 散户亏损研究的共性是：亏损集中在**单腿、付权利金、高 IV**的交易——这恰好是"缺口低开后（IV 高）买 put"的画像。多腿（例如 put debit spread）在多项研究中表现更好。
- OptionMetrics 观察到"高已实现波动日之后 VRP 可能反转"，缺口低开日往往伴随前一日或隔夜的高波动——这可能是买方相对不那么吃亏的场景，但需要自有数据验证。
- 散户限价单能显著降低实际成本（Bogousslavsky & Muravyev），说明对于你的执行，**用中间价附近的限价单而非市价单**是最直接的成本改进。

### Gaps
- 未找到专门研究"日内短持有（<2 小时）方向性买入 0DTE put"收益的学术论文；文献几乎都按持有至到期或 10:00 → 收盘计算。
- 未能读取 Khalil《Zero-Day-to-Expiry Options Trading and Variance Risk Premium》（[CBS PDF](https://research-api.cbs.dk/ws/portalfiles/portal/105671291/1775874_O._Khalil_Zero_Day_to_Expiry_Options_Trading_and_Variance_Risk_Premium.pdf)）和 SEC DERA 限价单论文的内容。
- 搜索摘要中提到某 0DTE VRP 工作论文称"无条件 0DTE 已实现 VRP 在所有 30 分钟区间均为正"，但摘录残缺、无法确定出处，未作为结论使用；**VRP 在开盘时段是否比午后更大**这一问题没有找到可靠来源。
- put 与 call 在 0DTE 短持有中的成本差异（如 put skew 溢价在开盘与午后的变化）未找到定量研究。

---

## 问题三：SPY 0DTE put 首小时实操微观结构——价差、theta、delta/gamma、行权价与结构选择

### Takeaway
SPY ATM 0DTE 的报价价差在盘中通常只有 $0.01–0.05（收盘前 15 分钟会放宽），以 $2–3 的 ATM 权利金计约为 1%–2% 的往返成本；在 IV 不变、标的不动时，ATM 0DTE put 从 10:00 起持有 30/60/90 分钟仅因时间流逝约损失 4%/9%/13%，盈亏平衡只需 SPY 约 0.1% 的有利波动——**theta 不是 30-90 分钟持有的主要杀手；开盘高 IV 的回落（vega）和 OTM 合约的相对价差更危险**。ATM 或略 ITM、限价单入场、或使用 put debit spread，是比裸买 OTM put 更稳健的选择。

### Cited Findings
- 交易博客（非同行评审）称 SPY ATM 0DTE 盘中价差通常 $0.02–0.05，收盘前 15 分钟可放宽至 $0.15–0.40；对比 SPX 约 $0.10–0.30；另一来源给出 SPY 0DTE $0.01–0.03 — [MarketXLS](https://marketxls.com/blog/how-to-trade-0dte-spy-options-expert-insights)；[QuantVPS](https://www.quantvps.com/blog/0dte-scalping-strategies)（搜索摘要中的博客数字，未逐一核对来源）
- 关于每小时 theta 的博客数字互相矛盾：有的说 10:00 时 ATM 每小时损失 $0.02、14:00 时每小时 $0.10；有的说下午 1 点是早盘衰减速度的 2 倍、2:30 是 3.5 倍；有引用 tastylive 数据称早盘每 $1 权利金约损失 25 美分；有的称 SPY $1.00 的 call 在第一小时即使不动也会损失 $0.30–0.50（与纯 theta 相比明显偏高） — [SPX Godfather](https://spxgodfather.com/theta-decay-0dte-options-hour-by-hour/)；[Volatility Box](https://volatilitybox.com/research/0dte-options-and-volatility/)（均为厂商/博客，数字不可靠）
- 厂商评论（GEXRadar，未注明来源、带推广性质）称 0DTE IV 在开盘前偏高、收盘时坍缩 — [GEXRadar](https://gexradar.io/blog/0dte-options-and-spx-volatility)
- 跳跃强度在开盘和收盘附近聚集，SPXW 0DTE 隐含的跳跃风险溢价大 — [Božović, SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/5223127.pdf?abstractid=5223127&mirid=1)
- Vilkov：bear put spread 与 put ratio spread 在高 VIX 状态下收益更高，call spread 类结构在低 VIX 状态更好；put ratio spread 的样本外 net Sharpe（0.93）在所有结构中最高（注意含裸卖 put 腿的尾部风险） — [GitHub 原文](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- 多项散户研究发现多腿 0DTE 交易显著优于单腿（但平均仍亏） — [Beckmeyer 等, ResearchGate](https://www.researchgate.net/publication/370012499_Retail_Traders_Love_0DTE_Options_But_Should_They)
- Almeida 等：OTM put 持有至到期的中位收益为 −100% — [FMA PDF](https://www.fma.org/assets/docs/Derivatives2025/Almeida.pdf)
- Option Alpha 的持续盈利者在约 10:15 ET 建仓、约 12:00 后平仓（主要为卖方结构） — [Option Alpha](https://optionalpha.com/blog/0dte-options-strategy-performance)
- 已发表的 SPY 日内趋势（"noise area"突破）策略：Zarattini, Aziz & Barbon《Beat the Market》报告 2007 年以来净 CAGR 20.8%、Sharpe 1.20（另一概述为 1.33，期间/成本假设不同） — [RePEc](https://ideas.repec.org/p/chf/rpseri/rp2497.html)；Concretum 有一篇把该信号的 SPY 头寸换成 0DTE 期权结构、评估成本与可实施性的文章，但未能取得其对比数字 — [Concretum Substack](https://concretumgroup.substack.com/p/intraday-trend-following-with-0dte)

### Inferences
以下为基于 Black-Scholes 近似（ATM 期权价 ≈ 0.4 × S × σ × √T）的**自行计算**，并非文献数字；假设 SPY = 600、IV = 20%、交易日 6.5 小时、10:00 ET 建仓：

| 时刻（剩余时间） | ATM put 理论价 | 相对 10:00 的时间损耗 |
|---|---|---|
| 10:00（6.0h） | ≈ $2.90 | — |
| 10:30（5.5h） | ≈ $2.77 | −4.4% |
| 11:00（5.0h） | ≈ $2.65 | −8.7% |
| 11:30（4.5h） | ≈ $2.51 | −13.4% |

- **theta 盈亏平衡：** 持有 60 分钟损失约 $0.25，ATM delta ≈ 0.5，只需 SPY 下跌约 $0.50（≈0.08%）即可覆盖 theta；再加上 $0.02–0.05 的往返价差，需要约 $0.55–0.60（≈0.1%）的有利移动。gamma（10:00 后 ATM gamma 约 0.06/$）会进一步帮助大幅下跌时的收益。结论：对 30-90 分钟持有，theta 并不致命。
- **注意 √T 是"时钟时间"假设。** 实际方差在开盘时段更集中（跳跃在开盘聚集），市场按"方差时钟"定价，首小时的真实衰减可能快于上表；建议用自有分钟级期权报价实测 10:00/10:30/11:00 的 ATM 价格与标的不变情形的对照。
- **vega 风险更大：** ATM 0DTE 权利金 ≈ 与 σ 成正比，IV 相对下降 10% → 权利金下降约 10%。在上述假设下，5:00 剩余时 vega ≈ $0.13 / 每 1 个波动率点；缺口低开日开盘 IV 往往偏高，若反弹失败后市场"横住"而非继续下跌，IV 回落 3–5 个点就会吃掉 $0.40–0.66，超过 1 小时的 theta。这意味着"方向对但幅度小"的情形，期权可能跑输做空 SPY。
- **价差的相对成本随行权价急剧上升：** ATM（权利金 $2–3、价差 $0.01–0.05）往返约 0.5%–2%；OTM（权利金 $0.30 左右、价差 $0.01–0.02）往返约 3%–7%。对 30-90 分钟持有，OTM 的相对价差 + 更高的 skew/VRP + 中位数归零的分布，使其期望值明显更差。
- **行权价/delta 建议：** 选择 ATM 至略 ITM（|delta| 0.45–0.60）。ITM 的 delta 更接近做空标的、theta/vega 占权利金比例更低，但绝对价差可能更宽；ATM 在 gamma 与成本间最均衡。避免 |delta| < 0.25 的 OTM 彩票型合约。
- **结构建议：** put debit spread（买 ATM、卖低 0.3%–0.5% 的 OTM put）可以：(1) 部分对冲开盘高 IV 回落的 vega 风险；(2) 卖出相对昂贵的 OTM skew；(3) 降低单腿付权利金 + 高 IV 这一散户亏损画像。代价是封顶尾部收益、两腿价差。Vilkov 的数据显示 bear put spread 在高 VIX 状态表现更好，与缺口低开日的特征吻合。
- **时间：** 避开开盘头几分钟（跳跃聚集、报价最不稳定）和最后 15 分钟（价差放宽）；你的"首小时 + 30-90 分钟持有"大致落在 9:45–11:30，属于价差较窄的时段。务必使用限价单（Bogousslavsky & Muravyev 的证据表明限价单能显著降低实际成本）。
- **做空 SPY vs 买 put 的取舍：** 做空 SPY 的成本几乎只有 $0.01 的价差（≈0.002%），远低于期权；期权的价值在于**风险塑形**（单笔最大亏损有限、跳空/急跌时收益放大），而非提升期望值。若标的回测为零 edge，用期权后的期望值大概率小幅为负；只有当策略选择出的情景系统性地"已实现波动 > 隐含波动"（例如负 gamma 日的急跌），long put 才可能优于做空标的。

### Gaps
- 未找到可靠的、按时段统计的 SPY 0DTE ATM put 实际价差与 theta 数据（博客数字互相矛盾）；Cboe/OPRA 或 ThetaData 分钟级报价可直接补足。
- 未取得 Concretum 关于"日内趋势策略改用 0DTE 期权实现"的对比数字（substack 无法访问）。
- 未找到关于 SPY（美式、实物交割）与 SPX/XSP（欧式、现金结算）在 0DTE 日内短持有上成本差异的定量研究。
- 未找到开盘时段 0DTE IV 的系统性日内路径（是否在缺口日开盘后回落）的学术证据，GEXRadar 的说法为无来源厂商观点。

---

## 问题四：0DTE 流量（客户净买 put/call、做市商 gamma）能否预测日内反转或趋势？可用的 regime 信号

### Takeaway
最有学术支撑的信号是**做市商净 gamma 的符号**：正 gamma → 日内反转增强、波动下降；负 gamma → 动量增强（Dim/Eraker/Vilkov；Adams 等；Baltussen 等 JFE 2021）。客户侧证据较弱：UBS 观察到 0DTE 交易者存在"逆势 delta 偏好"（跌时买 call 卖 put），进一步压制波动，但也警告在高波动期可能翻转为追跌买 put 从而放大下跌。没有找到同行评审的"客户 0DTE 净 put/call 买入预测日内收益"研究。

### Cited Findings
- 正的 MM 库存 gamma 增强日内价格反转，负 gamma 增强动量；MM 净 gamma 平均为正，与未来日内波动负相关 — [Dim, Eraker & Vilkov, SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190)（搜索摘要）
- 净 gamma 较高的日内区间之后，收益与后续订单流之间的反转关系更强；对冲需求的日内变化预测更强的订单流反转、更弱的动量、更低的波动 — [Adams 等, SSRN 5641974](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5641974)；[Quantpedia](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)（二手）
- 前 0DTE 时代：MM 净 gamma 为负时市场日内动量最强、为正时基本消失（同行评审） — [Baltussen 等, JFE 2021](https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598)
- UBS 衍生品策略师 Kieran Diamond（经 Bloomberg 报道，2026 年 10 月下旬）：战术型 0DTE 交易者在市场下跌时转向买 call、卖 put，上涨时相反（"counter-trend delta bias"），净效果相当于低买高卖，进一步压制指数波动；另一个压制因素是部分由机构卖出 1 天期 iron condor 导致的做市商 long gamma；UBS 认为这股逆势流量已大到压过做市商再对冲的影响；但他警告在高波动时期该动态可能逆转——若 0DTE 投资者转而追跌买 put，流量可能放大下跌并使做市商处于 short gamma — [Yahoo Finance / Bloomberg](https://finance.yahoo.com/markets/options/articles/zero-day-option-traders-betting-140000009.html)（未找到 UBS 原始报告）
- Cboe 称客户 0DTE 买卖接近平衡，做市商净 gamma 很小 — [Cboe Insights](https://www.cboe.com/insights/posts/volatility-insights-evaluating-the-market-impact-of-spx-0-dte-options)；而 Adams 等认为即便日度足迹小，日内对冲需求仍有影响 — [Interactive Brokers Campus](https://www.interactivebrokers.com/campus/traders-insight/securities/options/much-ado-about-0dtes-separating-fact-from-fiction/)（二者存在张力）
- Vilkov：已实现方差本身对 0DTE 策略 PNL 的解释力很低（最大 R² 约 4.5%），加入隐含方差与 skew 代理变量后 R² 增加约 2–7 个百分点；**已实现偏度（方向性移动）是主导渠道**；方向分类（logistic）优于直接预测收益；高 VIX 状态下 bear put / put ratio spread 收益更高 — [GitHub 原文](https://github.com/vilkovgr/0dte-strategies/blob/main/docs/paper/paper-annotated.md)
- Concretum 指出 2026 年对很多日内趋势模型（尤其 S&P 500）是困难的一年，并介绍了 J.P. Morgan 量化团队在 SOXX 趋势模型上叠加"卖出 ATM 0DTE 获取 carry"的方案，称显著改善 P&L 并平滑权益曲线（这是 JPM 的主张，非 Concretum 在 SPY 上的结果） — [Concretum Research 笔记](https://substack.com/profile/479204854-concretum-research/note/c-327273088)
- 厂商 GEX 指标（SpotGamma 等）提供"dealer gamma"估计，但其方法基于对谁是买卖方的假设、并不透明；相关学术研究使用的是带方向标识的 Cboe Open-Close 等数据 — [SpotGamma 0DTE 指南](https://spotgamma.com/0dte/)（厂商自述）；[LuxAlgo 对 SpotGamma 水平的解读](https://www.luxalgo.com/blog/spotgamma-levels-reveal-dealer-positioning/)（厂商）

### Inferences
- **可用于你策略的 regime 过滤（按证据强度排序）：**
  1. **MM 净 gamma 符号**（最强学术支撑）：只在估计为负 gamma 的日子做"反弹失败后的延续"put；正 gamma 日跳过或反向（做缺口回补）。公开可得的近似：厂商 GEX（需谨慎）、或自建——用 SPX/SPY 未平仓量按"客户净买、MM 净卖"的简化假设计算各行权价 gamma，并判断现价是否在大 put 持仓区之下。
  2. **VIX / 隐含波动水平**：Vilkov 显示高 VIX 状态下 put spread 类结构表现更好；同时高 VIX 往往对应负 gamma 环境。
  3. **前一日已实现波动**：OptionMetrics 观察到高 RV 之后 0DTE VRP 可能反转（期权相对便宜），对买方有利。
  4. **客户 0DTE 流向**（证据最弱、仅券商研究）：若盘中观察到 0DTE 客户由"逆势买 call/卖 put"转为"追跌买 put"，可能是从抑制转为放大的信号（UBS 的警告）——这正是你的反弹失败 put 策略最可能奏效的时刻。
- 价格层面的实操代理：缺口低开且开盘价/首个反弹高点位于前一日大量 put 未平仓行权价之下，往往意味着 MM 在该区域 short gamma，下跌更可能延续；若缺口落在大量 put 持仓行权价附近或上方（MM long gamma 区"钉住"），反弹失败后更可能横盘回归，此时买 put 会被 theta+vega 侵蚀。这一推论基于上述 gamma 文献的机制，未经直接检验。
- Concretum 提到 2026 年 S&P 500 日内趋势模型普遍困难，与"0DTE 时代正 gamma + 逆势散户流压制趋势"的叙事一致，也与你回测的零 edge 相符——说明该策略的边际改进更可能来自 regime 过滤而非执行工具的选择。

### Gaps
- 未找到同行评审研究直接检验"客户净 0DTE put/call 买入"对日内收益（尤其首小时）的预测力；UBS 结论仅见于媒体转述。
- 无法获得真实的 dealer 持仓（需 Cboe Open-Close / OPRA 带方向数据），厂商 GEX 估计的准确性没有独立验证。
- 未找到 SpotGamma / tastylive 等关于"负 gamma 日缺口延续率"的可核查数据研究。
- 2024-08-05、2025 年 4 月关税暴跌等极端日中 0DTE 流量是否放大下跌，未检索到系统性研究。

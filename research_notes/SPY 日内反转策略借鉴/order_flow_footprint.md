# Order-flow / Footprint 信号（aggressor delta、CVD 背离、absorption、imbalance）在 ES / SPY 日内反转中的实证证据

> 研究范围：ES / MES / SPY，2015-2026。目标是判断 order-flow 特征是不是 Umar "gap down 后开盘一小时反弹到 supply 区做空" 策略里 OHLCV 缺失的那块，以及怎样低成本检验。
> 方法说明：本次沙箱里 WebFetch 无法访问 arxiv.org（DNS 被网络 allowlist 拦截），所以下面大部分内容来自 WebSearch 的摘要和论文 abstract，没有逐页核对全文表格。凡是只在搜索摘要里看到、没有核对原文的数字，都已标注。

## 问题 1：学术证据（OFI、trade sign / signed volume、VPIN 及其批评、absorption / delta 背离；预测时距与衰减）

### Takeaway
Peer-reviewed 证据很强地支持 order-flow imbalance 对**同期**（contemporaneous）秒级价格变化的解释力（10 秒 mid-price 变化 R² 约 65%）。但作为**领先**（lagged）预测变量，它的效力很小，而且衰减极快：顶级研究给出的有效时距只有"约两次价格变化"、几秒到几分钟。没有找到任何 peer-reviewed 研究证明 delta 背离或 absorption 能预测 ES/SPY 日内高点后 30-60 分钟的反转。VPIN 的预测力本身也有激烈争议。

### Cited Findings

**OFI 与价格冲击（核心文献）**
- Cont, Kukanov & Stoikov 发现，短时间间隔内的价格变化主要由 best bid/ask 上的 order flow imbalance（OFI）驱动。两者是线性关系，斜率与 market depth 成反比 — [arXiv 1011.6402](https://arxiv.org/pdf/1011.6402)；[SSRN 1712822](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1712822)
- 他们用 2010 年 4 月 NYSE TAQ 中随机选的 50 只 S&P 500 成分股做 10 秒 mid-price 变化回归：OFI 的平均 R² 约 65%，trade imbalance（TI，即带符号成交量 / delta 一类变量）只有约 32% — [arXiv 1011.6402 v3 HTML](https://arxiv.org/html/1011.6402v3)（数字来自 arXiv 版本，期刊版可能有出入）
- 他们还认为，常被引用的 "square-root" 价格-成交量关系比基于 OFI 的线性关系噪声更大、更不稳健。期刊版发表在 Journal of Financial Econometrics 第 12 卷 47-88 页，年份在不同索引里标为 2013 或 2014 — [arXiv 1011.6402](https://arxiv.org/pdf/1011.6402)；[Imperial College 出版物页](https://www.imperial.ac.uk/mathematical-finance/research/research-publications/?respub-t4-action=citation.html&id=487955&noscript=noscript)
- Cont, Cucuringu & Zhang（Quantitative Finance, 2023）的结论有两点。一是在同期冲击上，用 multi-level OFI 之后再加入跨资产项，并不能提高解释力。二是在预测未来收益时，滞后的跨资产 OFI 能提高 out-of-sample R²，但这种滞后效应"主要出现在短期时距，并随时间快速衰减"。早期版本还报告，部分 out-of-sample 测试的 R² 是负的 — [Tandfonline 期刊版](https://www.tandfonline.com/doi/full/10.1080/14697688.2023.2236159)；[SSRN 3993561](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3993561)；[arXiv 2112.13213v1](https://arxiv.org/html/2112.13213v1)（具体的预测 R² 数值没能从全文表格核实）
- Kolm, Turiel & Westray（Mathematical Finance, 2023, "Deep Order Flow Imbalance"）用 LOBSTER 纳秒级数据，覆盖 115 只 Nasdaq 股票（2019-01-01 到 2020-01-31）。他们发现用 order flow（OFI）训练的模型明显优于直接用 order book 训练的模型，但单只股票预测的**有效时距大约只有两次平均价格变化**，alpha 在这个尺度达到峰值后就衰减 — [SSRN 3900141](https://papers.ssrn.com/abstract=3900141)；[Quantpedia 摘要](https://quantpedia.com/how-to-use-deep-order-flow-imbalance/)

**ES / SPY 本身的 order-flow 研究**
- Takahashi（2025, arXiv 2508.06788）用 E-mini S&P 500 的 1 秒 BBO 数据构造 OFI，在每个 15 分钟区间内估计一个用异方差识别的 structural VAR，把 OFI→收益的 price impact 和收益→OFI 的反向 flow impact 分开。结论包括：宏观数据公布时 price impact 上升、flow impact 下降（流动性暂时撤出）；即使不在公布时段，1 秒尺度的 returns-flows 结构关系在经济意义上也显著存在；朴素 OLS 会因反向因果而高估 price impact — [arXiv abs](https://arxiv.org/abs/2508.06788)；[arXiv HTML](https://arxiv.org/html/2508.06788)（没能读到全文数值）
- 美国 OFR 的一篇 working paper 研究了 ETF 与期货（即 SPY 与 ES 一类）的跨资产 order flow，发现两个市场的买（卖）OFI 都最稳定地对应正（负）的 ETF 和期货收益。所用收益度量是 10 毫秒和 1 秒级 — [OFR WP 19-04](https://www.financialresearch.gov/working-papers/files/OFRwp-19_04_cross-asset-market-order-flow-liquidity-and-price-discovery.pdf)
- 纽约联储 staff report（Overnight Drift）指出，E-mini 收益的自相关最多只在 30 分钟内显著 — [NY Fed SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- ECB working paper 研究宏观公布前的 E-mini 漂移，用截止到公布前 5 秒的 order flow，发现有漂移的公布日 order flow 的冲击和其他日子没有区别 — [ECB WP 1901](https://www.ecb.europa.eu/pub/pdf/scpwps/ecbwp1901.en.pdf)

**Signed volume / order imbalance 的领先预测（较早文献，主要是个股）**
- Chordia, Roll & Subrahmanyam（"Liquidity and Market Efficiency", JFE 2005）发现，滞后 order imbalance（OIB）能显著预测个股**5 分钟**收益，而过去的价格本身不能预测日内收益。他们把市场吸收 imbalance 的速度视为市场效率的体现 — [UCLA working paper PDF](https://www.anderson.ucla.edu/documents/areas/fac/finance/21-05.pdf)
- 同一组作者在市场层面（日频）做的研究结果较弱：大幅负 imbalance 日之后有反转，但大幅正收益加正 imbalance 日之后的反转很弱；在部分设定下 imbalance 没有预测力 — [UCLA "Order Imbalance, Liquidity, and Market Returns" PDF](https://www.anderson.ucla.edu/documents/areas/fac/finance/28-00.pdf)；[ResearchGate](https://www.researchgate.net/publication/222656835_Order_Imbalance_Liquidity_and_Market_Returns)
- 他们后续的研究（2008）被引用为发现：市场流动性高的日子里，order imbalance 的预测力更弱 — 同上，来自搜索摘要中的二手引用，未核实原文

**VPIN 及其批评**
- Andersen & Bondarenko 认为 VPIN 对短期波动率的预测很差，表面上的预测力主要来自它和成交强度之间的机械联系。他们还发现 VPIN 的历史高点出现在 2010 年 flash crash **之后**而不是之前，并且一旦控制 realized volatility，VPIN 对未来波动率的预测力就完全消失。他们认为 VPIN 之所以能"预测"波动率，是因为波动率上升会让 BVC（bulk volume classification）系统性地分错类。改用标准的 trade classification 后，VPIN 的表现正好和 ELO 的描述相反 — [SSRN 1881731](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1881731)；[ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1386418113000189)；[Aarhus CREATES RP 13-42](https://repec.econ.au.dk/repec/creates/rp/13/rp13_42.pdf)
- Easley, López de Prado & O'Hara 在 rejoinder 里反驳，说 VPIN 在 flash crash 前已经大幅上升（AB 也观察到了这一点），崩盘开始后继续上升也符合预期 — [ScienceDirect rejoinder](https://www.sciencedirect.com/science/article/abs/pii/S1386418113000293)；[Reflecting on the VPIN dispute](https://www.sciencedirect.com/science/article/abs/pii/S1386418113000475)

**Absorption / iceberg（与 footprint "吸收" 最接近的学术文献）**
- Zotikov（Devexperts）用一周左右 E-mini S&P 500 的全深度数据检测 CME iceberg 订单，估计 native iceberg 约占全部成交量的 4%，synthetic iceberg 占 3.3%-14.3% — [arXiv 1909.09495](https://arxiv.org/pdf/1909.09495)；[ResearchGate](https://www.researchgate.net/publication/335834705_CME_Iceberg_Order_Detection_and_Prediction)
- 另一篇发表在 Journal of Trading 上的 Globex 研究认为，GLBX 上的 iceberg 订单可以被检测和预测 — [Sierra Chart 托管 PDF](https://www.sierrachart.com/Download.php?Folder=SupportBoard&download=9733)；[PM Research](https://www.pm-research.com/content/iijtrade:::8:::3:::68.full.pdf?implicit-login=true&sigma-token=SvlFGhhdRVCYLYwzLfQ1aivO8uBAVvFQgFR5z38Gc-I)
- 有研究报告，市场参与者察觉到 iceberg 后会强烈地用 market order 去"吃"它；iceberg 被成交的比例越大，它的价格冲击越小 — 来自搜索摘要，原文出处没能逐一核实（见上面两篇 CME iceberg 文献的检索结果）
- 这次检索**没有找到**任何 peer-reviewed 研究检验"在支撑/阻力位检测到 iceberg 或 absorption 之后价格会可靠地反转"。也没有找到针对 ES/SPY 日内高点 CVD 背离的学术研究 — 检索结论，见上面的检索结果

### Inferences
- **时距错配是关键。** Umar 策略要的是 30-60 分钟的反转，而学术上 order flow 最强的证据是同期秒级（R² 约 65%）以及领先几秒到"两次价格变化"的预测。ES 自相关最多持续 30 分钟，CRS 的结果是 5 分钟级而且主要在个股上。所以"OFI 线性地预测未来 1 小时收益"基本没有文献支持。order flow 只可能以**条件型、事件型**信号的身份起作用：在特定结构位（开盘一小时高点、supply 区）上，买方力量耗尽或被被动卖单吸收。这是一个**没有被学术验证的假设**，不是已知效应。
- **Absorption 可以和 Cont 等人的线性冲击模型对接。** 他们证明 Δmid ≈ β·OFI，β 与 depth 成反比。footprint 里说的"absorption"（大量主动买入但价格不动）在这个框架下就是局部 price impact 系数 β 的骤降，也就是隐藏或被动 depth 的增加（iceberg 补单）。这给出了一个可以量化、可以检验的定义（见问题 4），而且比"看图判断吸收"客观得多。
- **Trade imbalance 弱于 OFI。** delta（trade imbalance）对同期价格的解释力只有 OFI 的一半左右（32% vs 65%）。footprint 只用成交数据（delta），丢掉了挂单撤单信息，所以理论上 footprint 信号比完整的 OFI 信号更弱。
- VPIN 之争说明，基于 BVC 的 "toxicity" 指标很容易把成交强度或波动率机械地当成预测力。任何 delta 类指标都应该先控制 realized volatility 和成交量，再看有没有增量信息。
- 买方力量在高点耗尽、被吸收，与日内反转之间的联系，在学术上最接近的是"流动性提供者吸收 imbalance 之后价格回归"（CRS 的效率观点、Takahashi 的 flow impact）。但这些研究都把反转放在秒到分钟级，不是小时级。

### Gaps
- Takahashi（2025）和 Cont-Cucuringu-Zhang 的具体数值（各时距的 price impact 系数、out-of-sample 预测 R²、衰减曲线）因 arxiv.org 被沙箱拦截，没能从全文核实。
- 没找到 2015-2026 年间专门研究 **ES 或 SPY 分钟到小时尺度** signed volume 领先预测力的 peer-reviewed 论文。可能有但没检索到，也可能根本不存在。
- 没检索 Gao, Han, Li & Zhou 的 "market intraday momentum"（SPY 开盘半小时收益预测收盘半小时）等与开盘时段相关的反向证据，本笔记不提供它们的数字。
- 没有找到任何关于"delta 背离 / absorption 在日内极值处预测反转"的学术研究。

## 问题 2：实务界证据（CVD 背离、stacked imbalance、absorption 的公开回测）

### Takeaway
实务材料几乎全是教学性的叙述和精选图例，没有样本量、样本外检验或显著性。没有找到任何严谨、可复现的 ES footprint 信号回测。少数出现的胜率数字没有方法说明，不可采信。

### Cited Findings
- NexusFi Academy 的几篇文章（CVD、delta divergence、divergence）用手选的图例讲 ES 上的看涨/看跌 CVD 背离，没有样本量、胜率或 p 值。其中一篇自己也说机械地套用"不会产生可靠结果" — [NexusFi: Delta Divergence](https://nexusfi.com/a/market-structure/delta-divergence-futures-trading)；[NexusFi: CVD](https://nexusfi.com/a/market-structure/cumulative-volume-delta)；[NexusFi: Divergence](https://nexusfi.com/a/indicators/divergence)
- 一份 ES scalping 指南称 delta divergence 是 ES "最可靠的短线反转信号之一"，但没有给出任何统计 — [TradeAlgo ES scalping guide](https://www.tradealgo.com/trading-guides/futures/es-futures-scalping-guide)
- JournalPlus 词条认为 cumulative delta 只在 ES 这类高流动性品种上有统计意义，并建议按品种典型的日 delta 区间来缩放背离阈值 — [JournalPlus: Cumulative Delta](https://journalplus.co/learn/glossary/cumulative-delta/)
- NexusFi 的 footprint 进阶文章写着"单个 stacked imbalance 胜率 48%，三个叠加时 85%"，但没有任何方法说明 — [NexusFi: Advanced Footprint Chart Patterns](https://nexusfi.com/a/strategies/advanced-footprint-chart-patterns)（不可采信）
- 平台文档（LuxAlgo、Quantower）把 300% diagonal imbalance 和 3 层 stacked 当作惯例默认值，同时提醒：冲进更大反向挂单的 imbalance "常常被吸收"；在薄的品种上，低成交量格子里的 300% 阈值会被噪声触发，需要加最小成交量过滤 — [LuxAlgo: Bid/ask Imbalance](https://www.luxalgo.com/library/concept/bid-ask-imbalance/)；[LuxAlgo footprint docs](https://docs.luxalgo.com/platform/charts/order-flow/footprint)；[Quantower blog](https://www.quantower.com/blog/imbalance-footprint-chart-and-rithmic-plugin)
- 实务界关于 iceberg 的建议（在 bid/offer 反复补单的隐藏流动性要结合 footprint 和 DOM 一起看）属于经验之谈，没有检验 — [Optimus Futures 指南](https://optimusfutures.com/blog/support-and-resistance-trading-guide/)

### Inferences
- 实务证据的质量相当于"轶事加幸存者偏差"。footprint 社区的阈值（300%、3 层、200-300% 区间）都是惯例，没有被优化或验证。用它们做第一轮检验是可以的，但不应该先验地相信它们有效。
- 回测一定会有过拟合风险：footprint 有大量自由参数（tick 聚合、bar 类型、阈值、窗口长度）。应该在样本内只固定少数几个预先登记的定义，然后在样本外验证。
- 实务界常说"信号要在关键位出现才有效"（LuxAlgo 的"被吸收"提醒、JournalPlus 的缩放建议）。这恰好支持 Umar 的做法：order flow 不是独立信号，而是对"gap down + 开盘一小时反弹 + supply 区"这一结构的**确认过滤器**。我们应该检验的是条件增量，也就是在同一 setup 里，有 order-flow 确认的交易是否明显优于没有确认的交易，而不是 order flow 本身的无条件 alpha。

### Gaps
- 这次检索没有找到 Jigsaw、Bookmap、Orderflows、QuantConnect 或学位论文中针对 ES footprint 信号的公开、带统计量的回测。不能排除存在付费或论坛内部的研究，但没有可引用的来源。
- Sierra Chart 用户论坛里可能有个人回测，但没能访问到可引用的内容。

## 问题 3：数据获取、成本与 trade classification 准确度

### Takeaway
ES/MES 的数据最干净也最便宜：CME MDP 3.0 本身带 aggressor side，Databento 按 GB 计量（CME 从约 $0.50/GB 起）就能拿到逐笔成交及主动方。SPY 在 SIP 层面没有 aggressor 字段，必须用 trades + NBBO quotes 跑 Lee-Ready 或 tick rule 推断，准确度大约 80-90%，在高频时段更差。所以先用 ES/MES 检验更划算。

### Cited Findings

**ES / MES（CME）**
- Databento 的 CME Globex MDP 3.0（GLBX.MDP3）历史数据按请求数据的未压缩字节计费（$/GB），CME 历史"从 $0.50/GB 起"，可以在下载前用 API 估价（`metadata.get_cost` / `list_unit_prices`）— [Databento GLBX.MDP3](https://databento.com/datasets/GLBX.MDP3)；[Databento Metered pricing](https://databento.com/docs/api-historical/basics/metered-pricing)；[Databento Futures](https://databento.com/futures)
- 第三方转述的 Databento CME 订阅价格是 Standard $199/月、Plus $1,750/月、Unlimited $4,500/月（Plus 和 Unlimited 是年约）— [FXMacroData vs Databento](https://fxmacrodata.com/articles/fxmacrodata-vs-databento)；[Databento 订阅价格更新](https://databento.com/blog/updates-to-subscription-pricing)。NexusFi 写的是约 $179/月，和前者冲突；还说按需历史数据约 $0.50-$2/GB，视 schema 而定 — [NexusFi: Databento for Futures Traders](https://nexusfi.com/a/data/databento-futures-market-data)（以官网为准）
- NexusFi 称 Standard 计划把 MBP-1、TBBO、Trades schema 的历史覆盖从 1 个月扩展到 15 年以上；完整 MBO 从 2017 年 5 月起，2010-2017 年最高粒度是 MBP-10 — [NexusFi](https://nexusfi.com/a/data/databento-futures-market-data)（第三方，未在官网核实）
- Databento trades schema 里有 `side` 字段，标记主动方：Bid 表示买方主动，Ask 表示卖方主动，None 表示没有标注。CME 的 implied trades 可能没有主动方，标准化后 `side` = None — [Databento trades schema](https://databento.com/docs/schemas/trades)；[Databento GLBX.MDP3 docs](https://databento.com/docs/venues-and-datasets/glbx-mdp3)；[ES 数据目录](https://databento.com/catalog/cme/GLBX.MDP3/futures/ES)

**SPY（美股）**
- Polygon.io 已于 2025-10-30 更名为 Massive.com，旧的 key 和 api.polygon.io 端点在过渡期继续可用 — [qveris 价格指南](https://qveris.ai/guides/polygon-pricing-optimized/)；[Massive changelog](https://massive.com/changelog)
- 个人非专业计划的价格说法不一：一份 2026 年 4 月的指南列 Basic $0、Starter $29、Developer $79、Advanced $199/月；另一来源（旧价格）中档为 $99/月。按这份指南，Developer 有 10 年历史和 trades，Advanced 增加 quotes 和 20 年以上历史 — [qveris 价格指南](https://qveris.ai/guides/polygon-pricing-optimized/)；[marketparquet 对比](https://marketparquet.com/vs/polygon)（以官网为准）
- Massive 称所有用户都可以免费获取含 trades 和 quotes 的每日历史 flat files（2024 年 3 月的博客），商业层提供 15 年以上的逐笔 trade 和 quote 历史 — [Massive: Flat files](https://massive.com/blog/flat-files)；[Massive: trading data](https://massive.com/landing/trading-data)

**Trade classification 准确度**
- Chakrabarty, Pascual & Shkilko（Journal of Financial Markets 2015, vol. 25）比较了 BVC、tick rule（TR）和 Lee-Ready（LR），这项研究用的是美股数据。BVC 在 1 小时 bar 上最高准确度为 79.7%，低于 TR（90.8%）和 LR（92.6%）— [IDEAS/RePEc](https://ideas.repec.org/a/eee/finmar/v25y2015icp52-79.html)；[ResearchGate](https://www.researchgate.net/publication/278795599_Evaluating_trade_classification_algorithms_Bulk_volume_classification_versus_the_tick_rule_and_the_Lee-Ready_algorithm)（数字来自搜索摘要）
- 有一项研究用报价和成交数据为 E-mini S&P 500 构建了准确的 trade classification 度量，摘要中出现 quote rule、tick rule、Lee-Ready 分别正确分类 76.4%、77.66%、81.05%。但搜索结果没法确认这组数字来自哪个数据集 — [Panayides/Shohfi 等 BVC 论文](https://tom.shohfi.com/don/pubs/01-Don-BVC.pdf)；[Easley, López de Prado & O'Hara "Discerning information from trade data", JFE](https://www.sciencedirect.com/science/article/abs/pii/S0304405X16000246)（**未核实**）
- 用已知真实发起方的 Euronext Paris 数据研究发现，Lee-Ready 在高成交强度时段表现更差；另一研究发现 LR 与 tick test 表现相当 — [Comparing Trade Flow Classification Algorithms in the Electronic Era](https://www.researchgate.net/publication/266673233_Comparing_Trade_Flow_Classification_Algorithms_in_the_Electronic_Era_The_Good_the_Bad_and_the_Uninformative)
- ELO 的 JFE 论文用数据中的 buy-sell indicator（交易所 aggressor flag）作为真值来检验分类算法，认为 tick rule 类算法在匹配主动方上更准，而 BVC 与信息交易的关系更紧密 — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X16000246)

### Inferences
- **先做 ES/MES 而不是 SPY。** CME 原生提供 aggressor side，免去了分类误差（SPY 用 LR/TR 有约 10-20% 的错分，而且开盘高波动时段更差，恰好是 Umar 交易的时段）。ES 和 SPY 在指数层面高度联动（OFR 论文也把两者当作同一价格发现系统），所以 ES 的结论可以直接用于 SPY 交易。
- **最低成本方案**（未逐项报价，请用 `get_cost` 确认）：在 Databento 上只请求 ES 前月合约的 `trades`（或 `tbbo`，每笔成交附带成交前的 BBO，可以算 OFI 的简化版和 microprice）schema，并只截取美东 09:30-10:30（加上 gap 计算所需的前一日收盘），覆盖 2-3 年，再筛出满足 gap down 条件的日子（一年大概几十天）。按日期和时段截取能把字节量压到全天全量数据的一小部分。成本大概率在几十到低几百美元的量级，但**这是推断，没有确认**。
- 如果要做真正的 OFI 或 absorption（需要看 best-level 挂单的增减），至少需要 MBP-1/TBBO；要识别 iceberg 补单则需要 MBO（2017-05 之后才有）。
- Rithmic、IQFeed、Kinetick 更适合实时盘中或平台内回放（Sierra Chart、NinjaTrader 的 footprint 回放），不适合批量研究，而且本次没有找到它们的历史数据价格。

### Gaps
- 没有拿到 Databento ES `trades` / `tbbo` / `mbp-1` 的具体 $/GB 单价，也没有拿到每日数据量（GB/天），所以无法给出 1-3 年历史的精确报价。需要在 Databento 账户中用 `metadata.get_cost` 确认。
- Rithmic、IQFeed、Kinetick 的历史 tick 数据价格和可回溯深度这次没有检索，没有可引用的数字。
- NYSE TAQ（WRDS 或直购）的价格没有检索。
- Databento 是否覆盖 MES 的完整历史（MES 于 2019 年上市）、哪个 CME tag 映射到 `side` 字段，都没有核实。
- 2015 年后在 ES 上用交易所 aggressor flag 作为真值的分类准确度研究，没有拿到可靠的具体数字（76.4%/77.66%/81.05% 那组数字的数据来源没有核实）。

## 问题 4：如何定义可检验的特征（delta、CVD 背离、absorption、bid/ask imbalance），以及已发表的参数

### Takeaway
已发表的参数只有两类。学术界有 Cont 等人严格的 OFI 定义；实务界的 footprint 惯例是 300% diagonal imbalance、3 层 stacked、加最小成交量过滤，没有经过验证。下面给出一组可以预先登记、可以直接写代码的定义，并把"absorption"量化成局部 price impact 系数的塌缩，以便用 2-3 年 ES 数据做低成本的条件增量检验。

### Cited Findings
- **OFI（Cont, Kukanov & Stoikov）**：基于 best bid/ask 价格和挂单量的事件级变化来累计 OFI，用它回归 mid-price 变化，并且用 depth 归一化（冲击斜率与 depth 成反比）— [arXiv 1011.6402](https://arxiv.org/pdf/1011.6402)；[Kukanov 讲稿 PDF](https://www.smallake.kr/wp-content/uploads/2016/05/Kukanov.pdf)
- **Multi-level / integrated OFI**：Cont-Cucuringu-Zhang 把 OFI 扩展到多档并做整合，多档 OFI 对同期冲击的解释力更好 — [Tandfonline](https://www.tandfonline.com/doi/full/10.1080/14697688.2023.2236159)
- **Diagonal imbalance 惯例**：把某价位的主动买量和低一个 tick 的主动卖量做比较，一方达到另一方的 3 倍（300%）即算 imbalance，这是 ATAS、Sierra Chart、NinjaTrader footprint 的默认值；连续 3 个及以上同向 imbalance 格子算 stacked imbalance（LuxAlgo 默认最少 3 行）— [LuxAlgo: Bid/ask Imbalance](https://www.luxalgo.com/library/concept/bid-ask-imbalance/)；[LuxAlgo footprint docs](https://docs.luxalgo.com/platform/charts/order-flow/footprint)
- 实务中阈值多在 200-300% 之间调整，短周期（如 5 分钟图）有人用 250-300%，并建议加最小成交量过滤以免在低量格子上被噪声触发 — [Quantower blog](https://www.quantower.com/blog/imbalance-footprint-chart-and-rithmic-plugin)；[TradingView 脚本说明](https://www.tradingview.com/script/YusfBJDb-Ultimate-Orderflow-Diagonal-hsitorical-Liquidity)
- CVD 背离阈值应按品种典型的日 delta 区间缩放 — [JournalPlus](https://journalplus.co/learn/glossary/cumulative-delta/)
- BVC（VPIN 使用的分类法）在波动率上升时会产生系统性错分，所以不应该用它来构造 delta — [SSRN 1881731](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1881731)

### Inferences
以下是基于上述文献和惯例设计的**建议定义**（本笔记的推断和设计，不是已发表的参数）。数据为 ES 前月合约的 Databento `trades`/`tbbo`，`side`=Bid 记为主动买，Ask 记为主动卖，None 的成交剔除并记录占比。

1. **Delta per bar**：`delta_t = Σ vol(side=Bid) − Σ vol(side=Ask)`，bar 用 1 分钟或 5 分钟。标准化：`delta_z = delta_t / rolling_std(delta, 过去 20 个交易日同一时段)`，以消除开盘时段成交量的季节性。同时保留 `delta_ratio = delta_t / total_vol_t`。
2. **CVD 背离（在新高处）**：从 09:30 开始累计 CVD。当价格创开盘以来新高 H2，且 H2 高于前一个摆动高点 H1 至少 k 个 tick（例如 2-4 tick），但 `CVD(H2) − CVD(H1) ≤ −θ` 时，记一次背离；θ 取过去 20 日开盘一小时 CVD 区间的某个分位（例如 25%），依照"按日 delta 区间缩放"的建议。更弱的版本是 CVD(H2) ≤ CVD(H1)。
3. **Absorption（把 footprint 的"吸收"量化）**：
   - 版本 A（成交-only，footprint 风格）：在价位 p（或 p±1 tick），过去 N 分钟（例如 3-5 分钟）的主动买量 ≥ 该时段每个价位主动买量分布的第 95 分位，而之后 M 分钟（例如 5 分钟）的最高价不超过 p + 1 tick。
   - 版本 B（Cont 框架，需要 `tbbo`/`mbp-1`）：滚动估计 `Δmid = β·OFI` 的局部斜率 β，或者算"每单位正 delta 带来的价格前进" = `Δprice / Σ正 delta`。absorption 定义为价格接近开盘一小时高点或 supply 区时，β 降到当日开盘以来的低分位（例如 < 20%），同时 OFI/delta 仍然为正且偏大。这直接对应"斜率与 depth 成反比"：吸收就等于隐藏或被动 depth 变大。
   - 版本 C（需要 MBO，2017-05 以后）：在 best ask 同一价位检测 iceberg 式补单（被吃掉后同价位立即补回），作为被动卖方的直接证据（参考 Zotikov 的检测思路）。
4. **Diagonal / stacked imbalance**：按惯例，ask 侧在价位 p 的主动买量 ≥ 3 × 价位 p−1 tick 的主动卖量，且两格成交量之和 ≥ 最小量（例如该时段每格成交量的中位数）时记为 buy imbalance；同一根 bar 内连续 ≥ 3 格同向记为 stacked。对 Umar 做空 setup，重点看高点附近是否出现 sell-side stacked imbalance，或者 buy-side stacked imbalance 之后价格不再上行（"失败的 imbalance"）。
5. **Bid/ask 挂单不平衡**（需要 `mbp-1`/`mbp-10`）：`QI = (bid_sz − ask_sz) / (bid_sz + ask_sz)`，可以加上多档加权版本，作为 OFI 的辅助。

**建议的检验设计（低成本）**
- 事件集：沿用我们已有的 OHLCV 版 Umar setup（gap down、开盘一小时反弹进 supply 区或前高，触发做空），这样 order-flow 只当作附加过滤器。样本主体放在 2023-2026（数据最便宜也最贴近现在），2017-2022 留作扩展或样本外。
- 主检验：在同一批 setup 内，比较"有 order-flow 确认"（例如定义 2 或 3B 成立）与"无确认"两组之后 30/60 分钟的收益（或到收盘的 R 倍数），用 permutation 或 bootstrap 检验差异。同时报告胜率、期望值、MAE/MFE，以及扣除 MES 往返成本和 1 tick 滑点后的结果。
- 防过拟合：预先登记 2-3 个定义和 1 组阈值（直接用惯例值 300%、3 层、95 分位），不做网格搜索；对多个定义做 Bonferroni 或 FDR 校正。
- 对照：控制同时段的 realized volatility 和成交量（吸取 VPIN 争议的教训），检查 order-flow 特征的增量信息是不是只是"高成交、高波动"的代理。
- 解读标准：鉴于学术证据显示 order-flow 的领先预测力在秒到分钟内衰减，若在 30-60 分钟的收益上看不到有确认组和无确认组之间的分离，应把它解读为"order-flow 确认不能挽救这个 setup"，而不是去调参。

### Gaps
- 没有找到已发表的、针对 CVD 背离或 absorption 的经过统计验证的参数（窗口、阈值）。上面的 k、θ、N、M、分位数都是建议的起点，不是文献值。
- 没有找到已发表的、把 footprint 信号和 Cont 式 β 塌缩联系起来的研究。版本 3B 的定义是本笔记的推断。
- 没有核实 Databento `tbbo` 在 CME 上能否完整重建 best-level 挂单的增减（严格的 OFI 可能需要 `mbp-1` 的逐事件更新），需要在文档中确认。

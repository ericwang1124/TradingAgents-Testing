# 美股指数（SPY / ES / SPX）日内动量 vs 日内反转：学术与实务证据（面向开盘一小时策略）

> 背景：我们回测（SPY 1 分钟 K 线，2019-2026）的规则型“gap-down 开盘 → 缩量反弹进入 supply zone → 做空 / 买 0DTE put，仅限第一小时”的 fade 策略，所有变体 Sharpe ≈ 0 或为负；在非 gap-down 日 fade 早盘上涨亏得更多（早盘上涨倾向于延续）；赢单与输单在入场时的价格/量/VIX/趋势特征上无法区分；FOMC/CPI/非农等事件日更差。
>
> 研究方法说明：本次沙箱中 WebFetch 对 www3.nd.edu、harbourfrontquant.substack.com、www.mql5.com 均解析失败（网络白名单限制），因此以下内容主要来自 WebSearch 返回的摘要/摘录及作者页面片段。凡是只能从二手摘要（Alpha Architect、CXO Advisory、Quantified Strategies、GitHub README、博客）得到的数字，均已标注“二手/未核实”。同行评审（JFE/JBF）与 SSRN 工作论文/博客回测已分开标注。

---

## 1. Gao, Han, Li & Zhou (2018, JFE) "Market intraday momentum"：规则、样本、R²、经济价值，以及样本外复现/失效

### Takeaway
同行评审证据（SPY 1993-2013）显示：首个半小时收益（含隔夜，即前收盘→10:00）对最后半小时（15:30-16:00）收益有正向预测力，但 R² 只有约 1.6%，择时年化毛收益约 6%+；效应在高波动、高成交量、衰退期和重大宏观数据发布日更强（FOMC 日 R² 约 11%，二手数据）。我们没有找到针对 2013 年以后 SPY 的同行评审子样本检验；唯一找到的近期检验（非同行评审博客，2022-04 起 1,085 个 SPX 交易日）称该效应已接近于零。

### Cited Findings
**原论文（同行评审，JFE 2018, vol.129(2), pp.394-414）**
- 发表信息：Journal of Financial Economics, 2018, 129(2): 394-414；作者 Lei Gao, Yufeng Han, Sophia Zhengzi Li, Guofu Zhou — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)；[SSRN 2440866](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)
- 样本与核心结论：基于 1993-2013 年 S&P 500 ETF（SPY）高频数据，首个半小时收益预测最后半小时收益；预测力在样本内与样本外都统计显著 — [SSRN 摘要](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)；[WashU 研究档案](https://profiles.wustl.edu/en/publications/market-intraday-momentum/)
- 条件性：预测力在“更高波动日、更高成交量日、衰退期、重大宏观新闻发布日”更强 — [SSRN 摘要](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)
- 推广：在另外 10 个最活跃的美国及国际 ETF 上也存在日内动量 — [Quantified Strategies 转述](https://substack.com/@quantifiedstrategies/note/c-151224359)（二手）
- 理论解释：与 Bogousslavsky (2016) 的“不频繁再平衡”模型一致，也与“临近收盘交易迟到信息”的模型一致 — [Quantified Strategies 转述](https://substack.com/@quantifiedstrategies/note/c-151224359)（二手）

**R² 与经济价值（数字在不同版本/转述间不一致，需以 JFE 正式版为准）**
- 工作论文版：首个半小时对最后半小时的预测 R² 为 1.6% — [工作论文 PDF（SSRN-id2440866 镜像）](https://www.smallake.kr/wp-content/uploads/2015/01/SSRN-id2440866.pdf)；[Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- 早期草稿样本 1999-2012：样本内 R² 约 0.02，样本外 R² 约 0.018；样本外 R² 在另一版本文本中为约 1.2%，又一版本为 1.7%（版本间不一致） — [CXO Advisory](https://cxoadvisory.com/calendar-effects/first-and-last-half-hours-of-trading-linked)；[Semantic Scholar 工作论文页](https://www.semanticscholar.org/paper/Intraday-Momentum:-The-First-Half-Hour-Return-the-Gao/ddc6180aff2e1dc6f75eac80d5d586d58c8039eb)
- 加入第 12 个半小时（15:00-15:30）收益作为第二预测变量后 R² 升至 3.5%；在首个半小时高波动日，两变量合计 R² 达 4.8% — [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)（二手，转述工作论文）
- 择时规则（早期草稿）：首个半小时收益为正则在最后半小时持有 SPY、为负则持现金，年化毛收益 6.3%；对照“每天最后半小时都持有”为 −0.5% — [CXO Advisory](https://cxoadvisory.com/calendar-effects/first-and-last-half-hours-of-trading-linked)（二手）
- QuantConnect 引用作者数字：SPY 样本期平均年化收益 6.67% — [QuantConnect Intraday ETF Momentum](https://www.quantconnect.com/learning/articles/investment-strategy-library/intraday-etf-momentum)（二手）
- 均值-方差投资者的 certainty equivalent return（CER）增益约 6.02%/年 — [Quantified Strategies 转述](https://substack.com/@quantifiedstrategies/note/c-151224359)（二手，未在原文中核实）
- FOMC 发布日 R² 约 11.0%，择时年化 20.04% — [Quantified Strategies 转述](https://substack.com/@quantifiedstrategies/note/c-151224359)（二手，多处转述相同数字，但未在原文中核实）

**后续复现 / 失效 / 其他市场**
- 跨市场正向复现（同行评审）：Baltussen et al. (2021, JFE) 用 1974-2020 年 60+ 个期货（股指、债券、商品、外汇）发现“市场日内动量无处不在”（见第 2 节） — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)
- 学位论文（非同行评审、不同样本）：首个和/或倒数第二个半小时收益在样本内外都能显著预测最后一小时收益，但把两者合并并不能提高对最后半小时的预测力（与 Gao et al. 的 3.5% R² 结论不同） — [DiVA 学位论文](https://www.diva-portal.org/smash/get/diva2:1878991/FULLTEXT01.pdf)
- 近期失效迹象（非同行评审博客，方法未核实）：作者称在 2022-04 以来 1,085 个 SPX 交易日（“0DTE 时代”）上重测，斜率接近零、每一年都不显著且符号交替 — [dev.to / firmtape](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0)
- 个股层面（间接相关）：EFMA 2024 会议论文称其研究的“最后半小时”模式比 Heston et al. (2010) 的美国证据弱约 75% — [EFMA 2024 论文](http://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2024-Lisbon/papers/Interday_Cross_Sectional_Momentum.pdf)

### Inferences
- 预测关系的方向是“早盘方向在尾盘被再确认”，而不是“早盘方向在 10:00-11:00 被反转”。Gao et al. 并未直接检验第一小时内的延续/反转，但它提供了一个与我们回测相容的事实：早盘方向（含隔夜缺口）不倾向被当天抹平。
- 对我们的 setup 有一个细节含义：在 gap-down + 早盘反弹日，Gao 的预测变量（前收盘→10:00）往往仍为负（缺口大于反弹幅度时），它预测的是“尾盘偏弱”，而不是“10 点前后的反弹立刻失败”。也就是说，如果想表达“看空 gap-down 日”的观点，文献更支持在 15:30 依据 r(前收盘→10:00) 的符号入场，而非在第一小时内逆势 fade（推断，需回测验证）。
- R² ~1.6% 意味着单日几乎不可预测，必须依靠大量交易次数和极低成本才能兑现；任何 0DTE 期权实现（theta、IV、点差）都可能吃掉这一量级的优势（推断）。
- 事件日：原文指出宏观新闻日动量更强（FOMC 日 R² 约 11%，二手），与我们观察到“事件日 fade 更差”方向一致。

### Gaps
- 未能抓取 JFE 正式版全文，故正式版的 R²、t 值、CER、手续费敏感性等精确数字无法核实；上表多为工作论文或二手转述，版本之间存在矛盾（样本 1993-2013 vs 1999-2012，OOS R² 1.2% / 1.7% / 1.8%）。
- 没有找到任何同行评审的“2013 年后 / 发表后”SPY 子样本检验；harbourfrontquant 的复现文章（可能含分期结果）因网络限制无法抓取。
- 首个半小时的精确定义（前收盘 16:00 → 10:00，含隔夜）来自任务描述与对原文的一般了解，本次检索片段中未逐字核实。
- 未检索到 Elaut, Frömmel & Payne（外汇）、Li, Sakkas & Urquhart（全球股指）等其他市场复现的具体数字。

---

## 2. Baltussen, Da, Lammers & Martens (2021, JFE) "Hedging demand and market intraday momentum"：dealer gamma / 杠杆 ETF 再平衡，何时动量、何时反转

### Takeaway
同行评审证据（60+ 期货，1974-2020）把指数日内动量归因于“空 gamma 对冲需求”（期权做市商、杠杆 ETF 再平衡在价格方向上追单）：S&P 500 的日内动量只在期权做市商净 gamma 为负（NGE<0）时存在且随负值加深而增强，NGE 为正时不显著；预测力在随后几天反转。后续 0DTE 研究（SSRN，非同行评审）进一步发现做市商净 gamma 平均为正，正 gamma 强化日内反转、负 gamma 强化动量——但“gamma 对冲是主要渠道”在学术上仍有争议。

### Cited Findings
**原论文（同行评审）**
- 发表信息：Journal of Financial Economics, 2021, 142(1): 377-403 — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)；[SSRN 3760365](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)；[Erasmus 机构库](https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/)
- 样本与结论：1974-2020 年 60+ 个期货（股票、债券、商品、外汇）的日内收益中，“市场日内动量”普遍存在；最后 30 分钟收益由当日其余时段收益（rest-of-day, ROD）预测；预测力经济上和统计上高度显著，并在随后几天反转 — [Erasmus 机构库](https://pure.eur.nl/en/publications/hedging-demand-and-market-intraday-momentum/)；[RePEc 摘要](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)
- 方向：ROD 为正对应最后 30 分钟预期收益为正，ROD 为负对应为负 — [danfin.net 摘要](https://danfin.net/intraday-momentum-final-30-minutes)（二手）
- 机制：对冲空 gamma 头寸需要顺着价格方向交易，从而制造价格动量；与期权做市商、杠杆 ETF 的 gamma 对冲需求相关 — [SSRN 摘要](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)
- 条件性：用 S&P 500 指数期权构造负 gamma 暴露（NGE）代理；NGE 为负时指数存在日内动量、NGE 越负越强；NGE 为正的交易日没有显著日内动量 — [Alpha Architect 综述](https://alphaarchitect.com/hot-topic-does-gamma-hedging-actually-affect-stock-prices/)（二手）
- 期权/期货数据期间：S&P 500 指数期权与 E-mini 期货部分样本为 2003-07 至 2020-05 — 检索摘要引用自 [工作论文 PDF](https://academicweb.nd.edu/~zda/intramom.pdf)（未能直接打开）
- 个股层面的相关但不同现象：Baltussen, Da & Soebhag “End-of-Day Reversal” 发现个股尾盘反转，主要来自对日内输家的正向价格压力，与市场层面的日内动量不同 — [EOD Reversal 论文](https://academicweb.nd.edu/~zda/EOD.pdf)；[EFMA 2024 版本](http://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2024-Lisbon/papers/EndofDayReversal_withnames.pdf)

**0DTE / dealer gamma 后续研究（多为 SSRN 工作论文）**
- Dim, Eraker & Vilkov “0DTEs: Trading, Gamma Risk and Volatility Propagation”：做市商库存净 gamma 平均为正，且与未来日内波动负相关；正（负）的做市商 gamma 强化日内价格反转（动量） — [SSRN 4692190](https://papers.ssrn.com/sol3/Delivery.cfm/4692190.pdf?abstractid=4692190&mirid=1)
- Adams, Fontaine & Ornthanalai（0DTE 与波动）：0DTE 净 gamma 的变化预测随后数小时 10 分钟已实现波动更低；净 gamma 越高，订单流反转越强；0DTE gamma 的效应约为非 0DTE gamma 的 4 倍 — [论文 PDF](https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf)
- 反方证据：普林斯顿学位论文认为 0DTE 交易与日内波动有关，但证据不支持“gamma 对冲反馈”是主要机制 — [Princeton Thesis Central](https://theses-dissertations.princeton.edu/entities/publication/61115cd1-cb09-4a8b-9230-ff488fc2a386)

### Inferences
- 文献给出的“动量 vs 反转”切换变量最明确的是 dealer gamma 符号：负 gamma → 顺势（日内动量），正 gamma → 逆势（日内反转/波动抑制）。这是一个我们回测中未使用的特征，可能解释“赢单与输单在价格/量/VIX/趋势特征上不可区分”——真正的区分变量可能在期权仓位结构里（推断，需验证）。
- 但需注意时间结构：Baltussen 的预测是“当日已实现方向 → 最后 30 分钟”，gamma 对冲压力最集中在尾盘；它并未说明第一小时的 rally 会被正 gamma 抹平。Dim et al. 与 Adams et al. 的反转效应是在分钟到小时级别、以波动/订单流衡量，量级未必足以覆盖 0DTE put 的成本（推断）。
- 如果 2022 年后 0DTE 使做市商净 gamma 多数时间为正（Dim et al.），则理论上 2022 年后的日内反转应更常见；我们的 fade 在 2019-2026 依旧无效，说明要么效应量级太小，要么其作用时段/价格水平（如大额 OI strike 附近的 pinning）与“第一小时 supply zone”不重合（推断）。

### Gaps
- 未能获得 Baltussen et al. 的择时策略 Sharpe、t 值、杠杆 ETF 再平衡量级、以及“近期更强/更弱”的分期结果（工作论文 PDF 无法打开）。
- 检索摘要中还提到 Brogaard, Han & Won（0DTE 交易量 +1σ 对应波动高于均值 9.1%）、Amaya 等（2020-2023 年做市商 gamma 最多为年化日波动贡献 3.3 个百分点）、Cboe 估计（2023 年 dealer 0DTE 净 gamma 仅占 ES 日流动性的 0.04%-0.17%）——但未能定位到这些数字的一手来源页面，故不列入已引用事实；它们指向“gamma 效应量级可能很小”。
- 没有找到公开、可复现的“用 GEX 符号过滤开盘一小时 fade”的回测。

---

## 3. Lou, Polk & Skouras (2019, JFE) "A tug of war" 及隔夜-日内反转、开盘缺口反转证据

### Takeaway
Lou-Polk-Skouras 是**个股截面**结果（隔夜与日内各自延续、跨时段反转、持续多年），并非指数择时信号，对 SPY 开盘一小时的直接指导有限。指数期货层面最直接的同行评审证据是 Grant, Wolf & Yu (2005, JBF)：1987-2002 年 S&P 500 期货在大幅开盘变动后先有约 10 分钟延续、随后在开盘后半小时到一小时内显著反转（正向开盘更强），但扣除买卖价差后毛利润大幅缩水。2026 年一项 MNQ 期货的证伪研究发现开盘缺口 fade 在 09:30/09:45/10:00 入场净收益 ≈0 或为负。

### Cited Findings
**Lou, Polk & Skouras（同行评审，个股截面）**
- 发表信息：JFE 2019, 134(1): 192-213 — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:134:y:2019:i:1:p:192-213)；[LSE 工作论文 PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- 核心发现：个股层面存在强烈的隔夜收益延续与日内收益延续，以及相互抵消的跨时段反转，且持续数年 — [LSE Research Online](https://researchonline.lse.ac.uk/id/eprint/87481)
- 14 个交易策略中，每个策略的利润只来自一个时段：要么全部来自隔夜（反转策略与多种动量策略），要么全部来自日内，且两个时段的利润通常符号相反 — [LSE 工作论文](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)；[Alpha Architect](https://alphaarchitect.com/2015/02/overnight-momentum-vs-intraday-momentum/)
- 解释：不同投资者 clientele 分别主导不同交易时段 — [LSE 工作论文](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)

**隔夜-日内反转（期货截面，工作论文）**
- “Overnight-Intraday Reversal Everywhere”：做多隔夜收益弱的期货、做空隔夜收益强的期货；在股指、利率、商品、外汇期货中都成立；情绪、宏观新闻、市场不确定性无法解释 — [工作论文 PDF](https://assets.super.so/e46b77e7-ee08-445e-b43f-4ffd88ae0a0e/files/c953a0e6-e93e-4bf7-b839-45a90cedced4.pdf)
- 样本外日内超额收益，Sharpe 为传统反转策略的 2-5 倍 — [paperswithbacktest 摘要](https://paperswithbacktest.com/strategies/overnight-intraday-reversal-everywhere)（二手）；但该网站的第三方实现显示最大回撤 −97%、年化为负 — 同上
- 作者署名不一致：PDF 显示 Della Corte & Kosowski，而 Yang Liu 的个人页列为 Chun Liu, Tianyu Wang, Guofu Zhou, Yingzi Zhu 等合著 — [Yang Liu 研究页](https://yangliu-finance.github.io/research/)
- 前身：“Market Closure and Short-Term Reversal”（Della Corte, Kosowski & Wang）在股票与期货中记录类似的隔夜-日内反转 — [McGill PDF](https://www.mcgill.ca/desautels/files/desautels/dkw_2016.pdf)；[CXO Advisory](https://www.cxoadvisory.com/technical-trading/overnightintraday-return-reversal-trading/)

**开盘大幅变动后的反转（S&P 500 期货，同行评审）**
- Grant, Wolf & Yu (2005)，Journal of Banking & Finance 29(5): 1311-1327：1987-11 至 2002-09，S&P 500 期货在大幅开盘变动（过滤阈值 ±0.10%、±0.20%、±0.30%）后存在高度显著的日内反转，年度与星期几分组也显著 — [SSRN 689282](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=689282)；[ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426604000949)
- 时间结构：开盘后约 10 分钟显著延续，随后出现一长串显著反转；大幅开盘变动后的反转出现在开盘后半小时到一小时内；正向开盘变动后的效应更强 — [ResearchGate 摘要](https://www.researchgate.net/publication/222520781_Intraday_price_reversals_in_the_US_stock_index_futures_market_A_15-year_study)；[相关论文 PDF 对 Grant et al. 的引用](https://scispace.com/pdf/intraday-price-reversals-for-index-futures-in-the-us-and-137ieyy6y7.pdf)
- 成本：按买卖价差调整后毛利润大幅缩水，交易者能否持续获利不确定 — [SSRN 689282](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=689282)
- 更早的 US/香港指数期货研究（JBF 2000）称考虑交易成本后仍有获利机会（细节未核实） — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378426699000722)

**缺口回补 / gap fade（多为实务与博客，质量参差）**
- 2026 年 arXiv 证伪研究（MNQ 微型纳指期货，OHLCV 信号）：在 09:30、09:45、10:00 入场的 gap fade 净收益接近零或为负；基于前 30 分钟动量的“缺口延续做空”是最可信的 near-miss — [arXiv 2605.04004](https://arxiv.org/pdf/2605.04004)
- Quantified Strategies 的 SPY 缺口回补回测（2010-01 至 2012-08）：110 笔、98 笔盈利、平均每笔约 0.19%（样本小、年代旧） — [Quantified Strategies](https://www.quantifiedstrategies.com/gap-fill-trading-strategies/)
- NexusFi（未核实、内部矛盾）：小缺口（0.25-0.5%）首小时回补约 48%、中缺口（0.5-1.0%）约 38%、大缺口（>1%）约 22%；同页又称 ES >0.5% 缺口首小时回补约 65% — [NexusFi](https://nexusfi.com/a/concepts/fill-the-gap)
- StatOasis 标题观点：“S&P 500 opening gaps: direction is noise, size is the signal”；其“下跌缺口约 98% 回补、通常当日”的说法以收盘计而非首小时（口径存疑） — [StatOasis](https://statoasis.com/overfit/research/sp500-opening-gaps)
- SwingTradeBot SPY 页面：gap-down 1 个交易日内回补率约 26%，同页另一数字约 20%（矛盾） — [SwingTradeBot](https://swingtradebot.com/equities/SPY/gaps)

### Inferences
- 唯一同行评审的“开盘反转”证据（Grant et al.）样本止于 2002 年，那时开盘价格发现机制、ES 隔夜交易流动性与 2019 年后完全不同；即便当年存在，扣除点差后也不稳健。我们 2019-2026 年的负结果与 2026 年 MNQ 证伪研究方向一致：开盘 fade 在现代市场大概率无可交易优势。
- Grant et al. 的“先 10 分钟延续、再反转”结构提示：若要测试 fade，应以**大幅开盘变动**（而非缩量反弹进入 supply zone）为触发，并以开盘后 10-60 分钟为窗口；但 2019 年以后的数据需重新检验，且以 ES/SPY 真实成本计。
- 隔夜-日内反转是**截面**（跨资产相对强弱）策略，不能直接翻译为“SPY gap-down 后日内上涨”的单资产择时规则；我们观察到 gap-down 日 fade 反弹相对“没那么差”，与“单资产缺口方向在日内被延续/再确认”并不矛盾（推断）。
- 实务缺口回补统计口径混乱（首小时 vs 收盘、回补定义不同），且多为营销型网站，不宜作为规则依据。

### Gaps
- 未获得 Grant et al. (2005) 的具体交易规则表与扣费后收益；未核实 JBF 2000 US/香港论文的作者与成本假设。
- 未找到 2010 年以后、同行评审的 SPY/ES “开盘缺口方向 → 首小时延续/反转”检验。
- Lou-Polk-Skouras 对指数（而非个股）的含义未见直接检验。

---

## 4. Zarattini & Aziz 等（2023-2025, SSRN）：“Beat the Market”噪声区间动量与 ORB——精确规则、Sharpe、成本、样本与独立复现

### Takeaway
三篇均为 SSRN 工作论文（作者来自 Concretum Group、Bear Bull Traders 等实务机构，未经同行评审，全部为样本内）。“Beat the Market”在 SPY 2007-2024 报告净 Sharpe 1.33、年化 19.6%；独立样本外检验（2024-05 至 2026-03）显示 Sharpe 降至 0.39、总收益 9.4%（同期买入持有 29.5%），且下降统计显著。QQQ 5 分钟 ORB 在零滑点假设下 CAGR 33.2%，但独立复现显示盈亏平衡滑点仅约 2.2 美分/股，另一复现在五个指数 CFD 上“毛收益可复现、净收益为零”。核心信息：这些都是**顺势（突破）**策略——它们的存在本身就是对“早盘 fade”的反向证据，但其可交易优势在样本外显著衰减。

### Cited Findings
**“Beat the Market: An Effective Intraday Momentum Strategy for S&P500 ETF (SPY)”（Zarattini, Aziz, Barbon）**
- 版本：首版 2024-05-10，本版 2025-02-03；Swiss Finance Institute Research Paper No. 24-97 — [SFI](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy)；[SSRN 4824172](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4824172)
- 业绩（样本内）：2007 至 2024 年初，净成本后总收益 1,985%、年化 19.6%、Sharpe 1.33 — [Concretum 页面](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)；[SFI](https://www.sfi.ch/de/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy)
- CXO 标注：样本 2007-05 至 2024-04，最大回撤 −25%，假设交易摩擦，属样本内 — [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/)
- 独立核对：beta −0.07（Sharpe 1.33、alpha 19.6% 与原文一致） — [giovannibrusco 仓库 PR #1](https://github.com/giovannibrusco/zarattini-2024-momentum-spy/pull/1)
- Noise Area 定义：以当日开盘价为中心，宽度为过去 14 个交易日在相同时刻“距开盘价的平均绝对变动”；上轨针对 gap-down 做调整 — [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/)；[PazSheimy 仓库](https://github.com/PazSheimy/spy-intraday-momentum-oos)
- 入场：仅在纽约时间 10:00-15:30 的每个整点/半点检查；收盘价高于上轨做多、低于下轨做空 — [svettelnova 复现仓库](https://github.com/svettelnova/intraday-momentum-spy)
- 跟踪止损：多头在 max(上轨, VWAP) 下方离场，空头在 min(下轨, VWAP) 上方离场；收盘前平仓 — [svettelnova 复现仓库](https://github.com/svettelnova/intraday-momentum-spy)；[QuantConnect 论坛](https://www.quantconnect.com/forum/discussion/17091/beat-the-market-an-effective-intraday-momentum-strategy-for-s-amp-p500-etf-spy/)；[CXO Advisory](https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/)
- 仓位：2% 日波动目标，杠杆上限 4 倍；QuantConnect 评论者质疑 2% 的选择，并指出由于策略常处于空仓，2% 不能换算成 2%×√252 年化波动 — [QuantConnect 论坛](https://www.quantconnect.com/forum/discussion/17091/beat-the-market-an-effective-intraday-momentum-strategy-for-s-amp-p500-etf-spy/)
- 波动依赖：有效性依赖高波动市场环境 — [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/)（二手）
- 获 Quantpedia Awards 2025 第 4 名 — [FSI St. Gallen 新闻](https://fsi.unisg.ch/de/newsdetail/news/quantpedia-awards-2025-fsis-barbon-and-team-secure-4th-place-with-intraday-momentum-strategy/)

**独立复现 / 样本外**
- Sheimy Paz（SSRN 7290621，2026）：在 2015-2024 样本内复现 Sharpe 1.34；样本外（约 2024-05 至 2026-03）Sharpe 0.39，总收益 9.4% vs 买入持有 29.5%；仓库称 Sharpe 下降统计显著（p<0.001） — [SSRN 7290621](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7290621)；[PazSheimy 仓库](https://github.com/PazSheimy/spy-intraday-momentum-oos)
- giovannibrusco（SPY + ES，事前冻结参数的防过拟合协议）：ES（IB）与 SPY（Alpaca）相关 0.97；ES 数据 2024-05 至 2026-07；滑点敏感性测试中在 $0.005/股下 Sharpe 仍为 1.02；作者注明报告生成于提前收盘日修复之前，需要重跑 — [仓库](https://github.com/giovannibrusco/zarattini-2024-momentum-spy)；[PR #1](https://github.com/giovannibrusco/zarattini-2024-momentum-spy/pull/1)
- Justin Chuk（SSRN 7609644，NQ 期货变体）：2020 至 2026-07 一分钟数据，可执行规则净成本后每交易日 +$10.26，bootstrap 区间为正；止损成交多滑 1 个指数点即吃掉 22% 优势；日度 Sharpe 1.14 — [SSRN 7609644](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7609644)
- 评论：质疑时变噪声带除了增加交易成本外是否真的增加收益 — [Quantmacro Substack 评论](https://quantmacro.substack.com/p/paper-review-an-effective-intraday)
- 其他复现（结果未取得）：16 年 NQ 与 ES 期货扣费复现 — [VigorTas 仓库](https://github.com/VigorTas/beat-the-market-replication)；Larry Swedroe 关于样本外检验的文章 — [Swedroe Substack](https://larryswedroe.substack.com/p/when-beat-the-market-meets-the-real)；EdgeLab NQ 测试 — [EdgeLab](https://edgelabtrading.com/blog/zarattini-intraday-momentum-nasdaq/)

**“Can Day Trading Really Be Profitable? … Opening Range Breakout (ORB)”（Zarattini & Aziz, SSRN 4416622, 2023-04）**
- 研究 2016-2023 年 ORB 策略的盈利性 — [SSRN 4416622](https://papers.ssrn.com/abstract=4416622)
- 规则与业绩：QQQ 5 分钟 ORB，开盘 5 分钟后按方向做多/做空，每笔风险 1%，当日平仓；CAGR 33.2% vs 买入持有 14.9%（2016-01 至 2023-02，1,795 笔交易，**假设零滑点**） — [CXO Advisory](https://www.cxoadvisory.com/technical-trading/day-trading-with-an-opening-range-breakout-strategy)
- 作者页：在杠杆约束下 1,484% vs QQQ 169% — [Concretum](https://concretumgroup.com/can-day-trading-really-be-profitable/)
- 作者主张：配合杠杆或 3 倍杠杆 ETF（如 TQQQ）可获得显著超额 — [Semantic Scholar 摘要](https://www.semanticscholar.org/paper/Can-Day-Trading-Really-Be-Profitable-Evidence-of-in-Zarattini-Aziz/4d55f526cc56f08662cb8976796cd3b719ef6d2b)
- 独立复现（QQQ）：盈亏平衡滑点约 2.2 美分/股；NQ 确认过滤器单笔显著（t=2.05），但其 76% 的盈利来自 2022 年一年；含安慰剂对照与 bootstrap 置信区间 — [giovannibrusco ORB 仓库](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)
- 独立复现（NQ、SPX、Dow、DAX、FTSE 的 CFD）：“毛收益可复现，净收益为零” — [MQL5 博客](https://www.mql5.com/en/blogs/post/776235)（仅标题/摘要可见）

**“A Profitable Day Trading Strategy For The U.S. Equity Market”（Zarattini, Barbon, Aziz, SSRN 4729284）——个股 Stocks in Play ORB**
- 5 分钟 ORB，2016-2023，7,000+ 美股 — [SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284)；[Concretum](https://concretumgroup.com/a-profitable-day-trading-strategy-for-the-u-s-equity-market/)
- 只交易开盘 5 分钟相对成交量（RV）≥100% 的前 20 只“in play”股票；Sharpe 约 2.8、净收益 >1,600%（二手） — [Wikipedia: Andrew Aziz](https://en.wikipedia.org/wiki/Andrew_Aziz)
- QuantConnect 在 1,000 只股票宇宙上重建：Sharpe 2.4、beta 接近 0 — [QuantConnect](https://www.quantconnect.com/research/18444/opening-range-breakout-for-stocks-in-play/)

### Inferences
- 三篇 Zarattini 系列都是“顺着开盘/日内突破方向做”的策略，且最好的版本依赖**高相对成交量/高波动**——这恰与我们“缩量反弹 → 逆势做空”的设定相反。我们在非 gap-down 日 fade 早盘上涨亏得更多，与“早盘突破噪声区间后倾向延续”的结论一致（推断）。
- 可直接借用的不是其收益，而是其**过滤器**：价格在 Noise Area 之内=噪声（fade 至少不与动量信号冲突）；价格突破上/下轨=不平衡（不应 fade）。我们的 supply zone 入场若常发生在上轨之上，意味着系统性地与该动量信号对做（推断，需在我们的数据上标注验证）。
- 发表偏差/数据挖掘信号：参数（14 日、30 分钟检查点、2% 波动目标、4 倍杠杆）均非事前设定；作者有商业利益（日内交易教育/资管）；全部为样本内；样本外 Sharpe 从 1.33/1.34 跌到 0.39；ORB 优势对滑点极敏感（2.2 美分/股盈亏平衡），且大量利润集中在 2022 年这种高波动单边年份。应以“正面结果高估真实优势”为默认假设。
- Stocks-in-Play ORB 的优势来自个股层面的“in play”事件流，而指数（SPY/QQQ）ORB 的净优势在独立复现中接近零——说明“开盘区间”信息在指数上已被充分套利（推断）。

### Gaps
- “Beat the Market”的确切佣金/滑点假设（常见说法 $0.0035/股佣金 + $0.001/股滑点）在检索中**未能核实**，需查 SSRN 4824172 原文。
- 检索摘要提到“ES 期货复现未能成立、作者视为结果脆弱的信号”，但无法确认出自哪一来源，未列入事实。
- QQQ ORB 的止损具体设定（如开盘 K 线高低点 / 10% ATR）、目标（10R 或收盘）以及 TQQQ 结果未能核实。
- MQL5 复现与 harbourfrontquant 文章因网络限制无法打开，具体数字缺失；VigorTas、Swedroe、EdgeLab 的具体结论未取得。
- 未找到 QuantConnect/Quantpedia 官方对“Beat the Market”的独立回测数字。

---

## 5. 专门针对 fade/反转前 30-60 分钟（opening reversal）、opening range 均值回归、SPY/ES 日内 VWAP 回归的证据，以及 2020-2025 年的变化

### Takeaway
我们没有找到任何同行评审、扣成本、做过样本外检验且支持“在 SPY/ES 上 fade 前 30-60 分钟”的近期证据。最好的正面证据是 1987-2002 年的 S&P 500 期货开盘反转（Grant et al.），且扣点差后不稳健；最好的近期证据（2026 arXiv MNQ 证伪研究）发现 gap fade 与 ORB 变体都未通过检验。2020-2025 年的变化方向是：日内动量类策略在样本外显著衰减（Beat the Market OOS Sharpe 0.39；0DTE 时代首/末半小时关系接近零——博客证据），而 0DTE 带来的正 gamma 理论上有利于日内反转/波动抑制，但其量级与因果渠道仍有争议。

### Cited Findings
- S&P 500 期货（1987-2002）：开盘后约 10 分钟延续，随后在半小时到一小时内显著反转；正向开盘后更强；扣除买卖价差后毛利大幅缩水 — [SSRN 689282](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=689282)；[ResearchGate](https://www.researchgate.net/publication/222520781_Intraday_price_reversals_in_the_US_stock_index_futures_market_A_15-year_study)
- 2026 arXiv（MNQ 期货，系统性证伪研究）：gap fade 在 09:30/09:45/10:00 入场净收益 ≈0 或为负；“bar+15 的 ORB 做多”在 447 笔样本外交易上 T=0.88、平均净 +2.82 点，所有 ORB 变体被判为 FAIL；最可信的 near-miss 是基于前 30 分钟动量的缺口延续做空 — [arXiv 2605.04004](https://arxiv.org/pdf/2605.04004)
- 零售/轶事：作者称约 63 个交易日内日内反转率 44%，并描述“开盘 30 分钟 K 线位于前一日区间顶部/底部 20% 且成交量低于平均则 fade”的规则，但没有给出该规则的统计结果 — [dev.to / hollowdocker](https://dev.to/hollowdocker/28-intraday-reversals-in-3-months-the-sp-is-breaking-every-trend-following-system-i-run-3ajf)
- 2024-2026 样本外：“Beat the Market” SPY 样本外 Sharpe 0.39（vs 样本内 1.33/1.34），总收益 9.4% vs 买入持有 29.5% — [SSRN 7290621](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7290621)
- 0DTE 时代（2022-04 起 1,085 个 SPX 交易日）首半小时→末半小时斜率接近零、各年不显著且符号交替（博客，未核实） — [dev.to / firmtape](https://dev.to/firmtape/intraday-momentum-is-dead-in-the-0dte-era-we-measured-it-on-1085-spx-sessions-43g0)
- 0DTE 做市商净 gamma 平均为正，正 gamma 强化日内反转 — [Dim, Eraker & Vilkov, SSRN 4692190](https://papers.ssrn.com/sol3/Delivery.cfm/4692190.pdf?abstractid=4692190&mirid=1)；0DTE 净 gamma 越高订单流反转越强 — [Adams, Fontaine & Ornthanalai](https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf)
- NQ 期货噪声带动量 2020-2026 仍有正的净收益（每日 +$10.26，bootstrap 区间为正），但对止损滑点敏感 — [SSRN 7609644](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7609644)

### Inferences
- “开盘反转”与“日内动量”并不矛盾：前者（Grant et al.）是**开盘后 10-60 分钟、对大幅开盘变动的部分回撤**，后者（Gao/Baltussen/Zarattini）是**当日方向在尾盘或突破后的延续**。一个可同时容纳两者的模式是：大幅开盘变动 → 短暂延续 → 部分回撤（噪声区间内）→ 若重新突破则延续至收盘。我们的 fade 卖在“反弹进入 supply zone”，相当于赌“回撤后的再突破失败”，而文献对这一段没有支持（推断）。
- 2020-2025 年的证据整体指向：简单 OHLCV 规则（无论顺势还是逆势）在指数上的可交易优势都在被压缩；这与我们“赢单输单在入场特征上不可区分”的结果相符——可能只是没有可提取的信号（推断）。
- 0DTE put 作为执行工具会放大问题：日内反转若存在也是小幅（几十个基点量级），而 0DTE put 需要覆盖 theta、IV 和点差（推断；本次未检索到 0DTE 期权实现开盘 fade 的研究）。

### Gaps
- 未找到任何公开的、扣成本 + 样本外的 SPY/ES VWAP 均值回归回测。
- 未找到专门研究“opening range 均值回归”（与 breakout 相反）的同行评审论文。
- 检索摘要中提及“SPY 30 分钟 opening range 有 42% 的日子两侧都被突破（6 个月样本、软件厂商报告）”，但未能确认来源页，故未列入事实。
- 未找到按 2020/2021/2022/2023/2024/2025 分年报告的 SPY 开盘反转统计。

---

## 6. 预测“动量日 vs 反转日”的条件（波动、隔夜缺口大小、新闻日、成交量）及可借鉴/可测试规则

### Takeaway
文献中相对一致的切换条件：**高波动、高成交量、宏观新闻日（FOMC/CPI 等）、衰退期 → 日内动量更强**（Gao et al.）；**dealer 负 gamma → 动量，正 gamma → 反转**（Baltussen et al.; Dim et al.）；**大幅开盘变动 → 开盘后 10-60 分钟内部分反转**（Grant et al.，仅 1987-2002 证据）；**缺口大小比方向更重要**（实务，未核实）。我们“事件日 fade 更差、非 gap-down 日 fade 更差”的观察与前两条完全吻合。

### Cited Findings
- 高波动日、高成交量日、衰退期、重大宏观新闻发布日的日内动量更强 — [Gao et al. SSRN 摘要](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)
- 首个半小时成交量越高，预测力越强 — [Quantified Strategies 转述](https://substack.com/@quantifiedstrategies/note/c-151224359)（二手）
- 首个半小时高波动时，首个+第 12 个半小时合计 R² 达 4.8%（全样本 3.5%） — [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)（二手）
- FOMC 日 R² 约 11.0%、择时年化 20.04%；对 Michigan 消费者信心、GDP、CPI、FOMC 纪要等发布日效应更强 — [Quantified Strategies 转述](https://substack.com/@quantifiedstrategies/note/c-151224359)（二手，未核实）
- NGE 为负时存在指数日内动量且越负越强，NGE 为正时不显著 — [Alpha Architect 综述 Baltussen et al.](https://alphaarchitect.com/hot-topic-does-gamma-hedging-actually-affect-stock-prices/)
- 正（负）做市商 gamma 强化日内反转（动量） — [Dim, Eraker & Vilkov](https://papers.ssrn.com/sol3/Delivery.cfm/4692190.pdf?abstractid=4692190&mirid=1)
- 大幅开盘变动（±0.10/0.20/0.30% 过滤）后反转，正向开盘后更强 — [Grant, Wolf & Yu (2005)](https://www.sciencedirect.com/science/article/abs/pii/S0378426604000949)
- “Beat the Market”有效性依赖高波动环境 — [CXO Advisory](https://www.cxoadvisory.com/momentum-investing/complex-intraday-time-series-momentum-strategy-applied-to-spy/)
- 个股 ORB 只有在开盘 5 分钟相对成交量 ≥100% 的“in play”股票上有效 — [SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284)；[Wikipedia: Andrew Aziz](https://en.wikipedia.org/wiki/Andrew_Aziz)
- 缺口：“方向是噪声，大小是信号” — [StatOasis](https://statoasis.com/overfit/research/sp500-opening-gaps)（实务）；小缺口比大缺口更易在首小时回补（未核实，且同页数字矛盾） — [NexusFi](https://nexusfi.com/a/concepts/fill-the-gap)
- 缺口延续做空（以前 30 分钟动量为条件）是 MNQ 证伪研究中最可信的 near-miss — [arXiv 2605.04004](https://arxiv.org/pdf/2605.04004)

### Inferences

**对我们现有回测结果的解释（推断）**
- 事件日更差：与 Gao et al. “宏观新闻日动量最强”一致——事件日信息冲击会被持续定价到收盘，逆势 fade 正好站在错误一侧。
- 非 gap-down 日 fade 早盘上涨更差：与“开盘后方向延续 / 突破噪声区间后延续”的动量证据一致；gap-down 日的反弹至少是在“缺口回补”的部分回撤框架下，因而亏得较少。
- 赢单/输单不可区分：文献给出的有效切换变量（dealer gamma、相对成交量、事件日历、突破 Noise Area 与否、开盘变动幅度）大多不在我们的价格/量/VIX/趋势特征集中；也可能根本没有可提取信号。

**可借鉴/可测试的量化规则（均需在 SPY 1 分钟 2019-2026 数据上以真实成本、事前冻结参数、分年报告的方式检验；每条注明文献来源与证据强度）**
1. **Gao 尾盘择时（同行评审，样本止于 2013）**：15:30 根据 r(前收盘→10:00) 的符号做多/做空 SPY 至 16:00；变体：加入 r(15:00→15:30)，并只在首半小时高波动日或宏观事件日交易。用于检验“gap-down 日的看空观点是否应放到尾盘表达”。
2. **Baltussen ROD + gamma 条件（同行评审，样本止于 2020）**：15:30 根据 r(前收盘→15:30) 符号交易最后 30 分钟，仅在 dealer GEX/NGE < 0 时启用；对照 GEX > 0 的日子检验是否转为反转。
3. **Gamma 过滤的开盘 fade（SSRN 0DTE 证据）**：仅在 dealer 净 gamma 为正（且最好 0DTE 净 gamma 高）时允许 fade 早盘延伸；负 gamma 日禁止 fade 甚至翻转为顺势。需自建或采购 GEX 数据。
4. **Noise Area 作为 fade 的否决器（SSRN，OOS 衰减）**：用 14 日、同一时刻的平均 |价格−开盘价| 构造上下轨（上轨对 gap-down 用 max(开盘, 前收) 调整）；价格在 30 分钟检查点收于上轨之上时禁止做空；只在轨道内部的反弹做 fade。也可直接测试原版顺势规则（10:00-15:30 每半小时检查、max(上轨,VWAP) 跟踪止损、2% 波动目标、4 倍杠杆上限），以 2024-05 以后为纯样本外段（已知 OOS Sharpe 0.39）。
5. **Grant et al. 式大幅开盘变动反转（同行评审，1987-2002，扣费后不稳健）**：|开盘相对前收| ≥ 0.30%（同时测试 0.10%/0.20%）→ 等待 10 分钟 → 逆向入场 → 10:30 或 11:00 平仓；分正/负开盘、分年检验，尤其看 2020 年以后是否仍存在。
6. **缺口延续（而非缺口回补）做空（arXiv 2026，near-miss 而非通过）**：gap-down 且 09:30-10:00 收益为负 → 顺势做空至收盘或至 Noise Area 下轨跟踪止损。这是我们 setup 的镜像，值得作为对照组。
7. **事件日规则**：FOMC/CPI/NFP 日禁止 fade；或在这些日子仅允许顺势（与 Gao et al. 新闻日动量更强一致）。
8. **执行层面**：先在 SPY/ES 标的上验证信号，再考虑 0DTE；用 ORB 复现得到的盈亏平衡滑点（约 2.2 美分/股）与 NQ 研究中“1 点止损滑点吃掉 22% 优势”作为成本敏感性基准。

**数据挖掘与发表偏差提醒（推断）**
- 同行评审结果（Gao 2018、Baltussen 2021、LPS 2019、Grant 2005）样本均在 2020 年及以前结束；Zarattini 系列为实务机构 SSRN 工作论文、全部样本内、参数非事前设定，样本外已出现显著衰减；博客/营销网站（Quantified Strategies、NexusFi、StatOasis、SwingTradeBot、dev.to）数字口径不一、常有内部矛盾。
- 我们自己已对同一 setup 测试了大量变体（均为 Sharpe ≈ 0 或负），再在同一数据上加过滤器“救回”策略的风险很高；建议对上述任何新规则采用事前冻结参数 + 2024-05 之后作为纯样本外 + 分年稳定性检验（参照 giovannibrusco 的“ex-ante frozen”协议）。

### Gaps
- 未找到量化“隔夜缺口大小 → 当日延续/反转概率”的同行评审近期（2015 年后）SPY/ES 研究；实务数字互相矛盾。
- 未找到“开盘成交量（相对成交量）对 SPY 开盘反转/延续的条件效应”的指数层面研究（只有个股 Stocks-in-Play 证据）。
- 未找到 VIX 水平/期限结构作为指数日内动量 vs 反转切换变量的直接研究（只有“高波动日动量更强”的一般结论）。
- 公开 GEX 数据的质量与可得性、以及“GEX 过滤后开盘 fade”的实证，均未找到可靠来源。

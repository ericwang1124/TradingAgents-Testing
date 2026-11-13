# 中等下行趋势 + 中等隐含波动率下 S&P 500（SPY/ES/SPX）的日内与短周期（隔夜 / 1-5 日）行为

> 研究日期：2026-11-13。仅供研究，不构成投资建议。
> 方法说明：本沙箱的 WebFetch 对 newyorkfed.org、academicweb.nd.edu、bespokeinvest.substack.com、spytomorrow.com、benzinga.com 等域名全部 DNS 失败，因此**几乎所有数字都来自 WebSearch（extended）返回的摘要/片段，而非论文全文**。凡是只来自单一博客/厂商、方法不明、或摘要无法确认具体出处页面的数字，均在条目中标注【弱】或【出处待核】。
> 当前状态（用户给定）：SPY 低于 50 日 SMA 约 -0.9%、略低于 20 日线，5 个交易日反弹 +3.3%；VIX ≈ 18.7，期限结构 contango（VIX/VIX3M ≈ 0.93）；ATR ≈ 1.6%；通胀黏性、Fed 官员偏鹰、Nvidia CEO 离职冲击。自有回测（SPY 1 分钟，2019-2026）：逆势淡化早盘上涨亏钱（尤其 "down / VIX 15-20" 状态），顺势跟随单向（高 efficiency）的首 30 分钟走势最佳（OOS Sharpe ≈ 0.86）。

---

## Q1. 隔夜 vs 日内收益分解：隔夜溢价在下行趋势 / 高波动状态下是否改变？2020-2026 的新证据

### Takeaway
长期看美股指数的股权溢价几乎全部来自隔夜（尤其欧洲开盘前后几小时），日内收益接近零甚至为负；但这一溢价**高度依赖样本期、在 2021 年后明显衰减（NY Fed 作者本人 2026-07 确认"消失"）**，且在下行状态下方向不稳定：2022 年隔夜段跌得比日内更多（单一来源），而另一些"日内持续抛售"型回调中隔夜段反而跑赢。对当前状态而言，"隔夜持有"不能当作稳定的 regime-independent edge。

### Cited Findings
**经典文献（样本期）**
- Cliff, Cooper & Gulen (2008) "Return Differences between Trading and Non-Trading Hours: Like Night and Day"：用逐笔数据把收益拆成多个时段，1993–2006 年美股股权溢价基本全部来自隔夜（Night = 16:00→次日 9:30）；交易时段平均收益接近零、有时为负。二手摘要给出 S&P 500 成分股隔夜平均 0.028%–0.048%/日、日内 -0.028%–0.002%/日（取决于平均方法）；另一来源称其发现一周五天隔夜皆为正、日内三天为负。（注：有综述把样本终点写为 2003，终点年份不一致）— [ResearchGate 条目](https://www.researchgate.net/publication/228461243_Return_Differences_between_Trading_and_Non-Trading_Hours_Like_Night_and_Day)；[CXO Advisory 摘要](https://www.cxoadvisory.com/calendar-effects/buy-at-the-close-and-sell-at-the-open/)；[arXiv 2507.04481](https://arxiv.org/html/2507.04481v1)
- Kelly & Clark (2011) 用 ETF 在 1999–2006 年记录到类似的隔夜/日内差异（仅见二手引用，未见原文细节）— [arXiv 2507.04481（文献综述部分）](https://arxiv.org/pdf/2507.04481)
- Lou, Polk & Skouras (2019, JFE 134:192–213) "A Tug of War"：横截面上，reversal 与多种 momentum 策略的利润要么全部在隔夜、要么全部在日内获得，且两段常常符号相反；作者用"投资者异质性/clientele"解释隔夜与日内各自的持续性 — [IDEAS/RePEc](https://ideas.repec.org/a/eee/jfinec/v134y2019i1p192-213.html)；[Yale 工作论文版](http://www.econ.yale.edu/~shiller/behfin/2015-04-11/lou_polk_skouras.pdf)
- Lou, Polk & Skouras 后续 "The Day Destroys the Night, Night Extends the Day"：过去（平滑后的）隔夜市场收益**负向**预测随后的 close-to-close 收益（季度 R² > 14%），主要通过**日内均值回归**实现；均值回归主要发生在日内 clientele；中介机构风险承受度负向预测日内收益 — [LSE PDF](https://personal.lse.ac.uk/loud/LouPolkSkouras.pdf)；[Carlo Alberto PDF](https://www.carloalberto.org/wp-content/uploads/2023/01/Day-Destroys-The-Night-Night-Extends-The-Day.pdf)
- Bondarenko & Muravyev (JFQA 2023, 58(3):939–967) "Market Return Around the Clock: A Puzzle"：E-mini S&P 500 全天候交易数据显示，**欧洲开盘前后 4 小时贡献了全部平均市场收益**，该时段 Sharpe ≈ 1.6、扣成本后仍高；VIX 期货隔夜上升、在欧洲开盘附近下降（不确定性被"解决"）。二手资料称样本 1998–2018 — [Cambridge/JFQA](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3)；[ResearchGate](https://www.researchgate.net/publication/343386401_Market_Return_Around_the_Clock_A_Puzzle)；[行业笔记引用样本期](https://static1.squarespace.com/static/5bedbc974eddecbfbb0c217e/t/60f9c66d85ed7357cd00c600/1626981997756/PriceDiscovery-TacticsToTimeTrading-20210714-final.pdf)

**下行/抛售后的隔夜行为（与当前状态最相关）**
- Boyarchenko, Larsen & Whelan (RFS 2023, 36(9):3502–3547) "The Overnight Drift"：1998–2019 年 E-mini 样本中，最大正收益集中在美东 2:00–3:00（欧洲开盘），年化约 3.6%；**市场抛售之后会出现稳健的正向隔夜反转，而上涨之后的反转小得多（不对称）**；机制为 dealer 在投资者净卖出日吸收库存、隔夜持有库存获得补偿（inventory risk）。摘要片段还提到抛售后隔夜在亚洲时段平均 7.6%、欧洲时段 12.4%（年化口径，具体条件化方式未能核实）— [RePEc/RFS](https://ideas.repec.org/a/oup/rfinst/v36y2023i9p3502-3547..html)；[CBS 接受稿 PDF](https://research-api.cbs.dk/ws/portalfiles/portal/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf)；[Liberty Street 2021](https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns)
- 对该论文的讨论（Bogousslavsky, FMA 2022）质疑：其隐含的收盘价格冲击在图表中并不明显，且检验条件是收盘 order imbalance 而非收益本身 — [讨论稿 PDF](https://bogousslavsky.github.io/files/FMA_2022_discussion.pdf)
- **发表后衰减（关键）**：同一作者在 Liberty Street Economics 2026-07-01 发表 "The Disappearing Overnight Drift"：2:00–3:00 窗口此前约 3.7%/年，**自 2021 年以来平均接近零**；收盘 order imbalance 与隔夜收益的关系"已经瓦解"；作者从收盘 imbalance 离散度、收益方差水平、流动性提供者风险承载能力三个渠道解释（最终归因未能读到全文）— [Liberty Street 2026-07](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)；[Fed in Print](https://www.fedinprint.org/item/fednls/103479)
- 2022 熊市：某 SPY 研究（约 8,450 个交易日，1993 起）称 2022 年隔夜段 -14.7%、日内段 -5.6%；2023 年日内 +19.2% vs 隔夜 +4.3%；2024 年格局再翻转。【弱：单一来源、方法未披露；两段复合约 -19.5%，与 Yahoo 的 SPY 2022 全年总回报 -18.17% 不完全吻合，可能是股息/计算口径差异】— [spytomorrow.com](https://spytomorrow.com/spy-overnight-returns-vs-intraday/)；[Yahoo Finance SPY 业绩](https://finance.yahoo.com/quote/SPY/performance/)
- Bespoke "Constant Intraday Selling"：在一段较近期的回调中，6 个月内买入持有约 -5%，而"收盘买、开盘卖"（仅持有隔夜）+2.3%。【出处待核：帖子日期未能确认，WebFetch 被拦截】— [Bespoke Substack](https://bespokeinvest.substack.com/p/constant-intraday-selling)
- Robot Wealth：SPX/SPY 全周期大部分累计收益来自隔夜持有，2000 年以来日内总收益为负；隔夜-日内收益差在较短窗口内呈均值回归；另一篇文章指出美国股指**大部分大幅负收益发生在隔夜** — [Robot Wealth: overnight and intraday SPX returns](https://robotwealth.com/overnight-and-intraday-spx-returns/)；[Robot Wealth: revisiting](https://robotwealth.com/revisiting-overnight-vs-intraday-equity-returns/)
- Cowen 一则笔记把某两个月隔夜跑赢归因于"下跌交易日的实现波动更低、下跌交易日数量更少"【弱：摘要级】— [Cowen](https://www.cowen.com/?p=15482)
- 怀疑/成本视角：Alpha Architect 总结认为交易成本会抹掉隔夜收益异象；Knuteson 认为隔夜正/日内负的模式"可疑地一致"且原因未知；另有分析指出样本起止点稍改即显著改变结论 — [Alpha Architect](https://alphaarchitect.com/trading-costs-wipe-out-the-overnight-return-anomaly/)；[Knuteson arXiv 2010.01727](https://arxiv.org/pdf/2010.01727)；[arXiv 2507.04481](https://arxiv.org/html/2507.04481v1)
- TradingView 用户统计：SPY 三十余年隔夜累计 +1,105.62% vs 日内 +26.84%，但 p 值 0.054【弱：用户脚本，非同行评审】— [TradingView](https://www.tradingview.com/chart/SPY/5fk9yQhZ-The-Overnight-Wealth-Machine/)
- VIX 本身：1990–2022 年 VIX 隔夜变动始终为正、日内为负（与 Bondarenko-Muravyev 的"隔夜不确定性累积、日内消化"一致）— [Redfame 论文](https://redfame.com/journal/index.php/aef/article/download/5819/6020)

### Inferences
- 下行状态下隔夜溢价并不"自动变大"：有两种互相矛盾的子模式——(a) **新闻/宏观驱动、隔夜跳空下跌**型（如 2022 年 CPI/Fed 主导）中隔夜段更差；(b) **现金时段持续派发**型（Bespoke 所述"constant intraday selling"）中隔夜段跑赢。当前状态（通胀数据+Fed 鹰派讲话多在美东交易时段或盘前发布、外加单股冲击）更接近 (a) 与 (b) 的混合，无法先验判断。
- Boyarchenko 的"抛售日后买收盘、欧洲开盘卖"机制在理论上最契合"down 状态"，但作者自己报告 2021 年后该效应已接近零——应视为**已衰减的 edge**，若用，仅作为对日内策略的轻度 tilt，并需自有 2021-2026 数据验证。
- Lou-Polk-Skouras 的"day destroys the night"意味着：**大幅隔夜跳空后，日内更可能部分回吐**。这与用户自有发现（淡化早盘涨势亏钱）并不冲突：前者是隔夜跳空的日内回归，后者是开盘后首 30 分钟的日内方向延续——两者测量的时段不同，应在回测中把"gap"与"开盘后首 30 分钟（9:30–10:00）的 open-to-10:00 收益"分开处理（Gao et al. 的首 30 分钟收益是从**前收盘**算起，包含 gap）。

### Gaps
- 未找到对 SPY 隔夜/日内收益**按 VIX 分桶或按 50/200 日均线上下**拆分的可靠研究（只有 2022 单年的单一来源数字）。
- Boyarchenko 论文中"抛售后隔夜反转"的基点级数字和 2021-2026 衰减的具体归因未能读取（newyorkfed.org 被拦截）。
- Kelly & Clark (2011) 的具体数字、Bespoke 帖子的日期均未能核实。

---

## Q2. 日内动量（intraday momentum）与波动率/趋势的条件关系

### Takeaway
学术证据一致表明：首 30 分钟（含隔夜 gap）预测最后 30 分钟的"市场日内动量"在**高波动日、高成交量日、衰退期、重大宏观数据发布日更强**；机制上与 dealer **负 gamma** 对冲和杠杆 ETF 尾盘再平衡有关（负 gamma → 动量，正 gamma → 反转）。实践中常用"VIX > 20 才开启"之类过滤器。VIX ≈ 18.7 处于边界区：效应存在但不是最强区间。**未找到任何按均线趋势状态（above/below MA）拆分日内动量的研究。** 发表后衰减证据明显（Beat the Market OOS Sharpe 从 1.3 降到 0.39）。

### Cited Findings
- Gao, Han, Li & Zhou (2018, JFE 129(2):394–414) "Market Intraday Momentum"：SPY 1993–2013 高频数据，**首半小时收益（从前一日收盘起算）预测最后半小时收益**；在统计与经济上显著，且在**更高波动日、更高成交量日、衰退期、重大宏观新闻发布日更强** — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)；[EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)
- 早期工作论文版本（1999-01-04 至 2012-12-31）简单择时策略年化约 6.34% — [Alpha Architect](https://alphaarchitect.com/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- 跨国研究（Li, Sakkas, Urquhart 等）：首-末半小时关系在金融危机和衰退期更显著；美国首半小时收益还能预测其他市场的末半小时 — [Reading 大学接受稿](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf)；[Lancaster FoFI 2020 工作论文](http://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-092-Zeming-Li.pdf)
- Baltussen, Da, Lammers & Martens (2021, JFE 142(1):377–403) "Hedging Demand and Market Intraday Momentum"：60+ 期货、1974–2020，"intraday momentum everywhere"——收盘前最后 30 分钟收益被当日其余时段收益预测，且**该可预测性在随后几天反转**；机制为杠杆/反向 ETF 再平衡和期权做市商 gamma 对冲；用期权未平仓构建的做市商净 gamma（NGE）代理显示：**NGE 为负时存在指数日内动量，越负越强**；二手摘要称正 gamma 日无显著日内动量 — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)；[EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)；[Traders Magazine（作者撰文）](https://www.tradersmagazine.com/am/do-markets-burst-in-the-same-direction-in-the-last-half-hour-of-trading/)
- Beckmeyer 等：杠杆 ETF 再平衡资金集中于最后 30 分钟，再平衡流一个标准差的增加会显著提高尾盘收益 — [ResearchGate](https://www.researchgate.net/publication/355381896_The_Role_of_Leveraged_ETFs_and_Option_Market_Imbalances_on_End-of-Day_Price_Dynamics)；[FMA 会议稿](https://fmai.memberclicks.net/assets/docs/Derivatives2021/beckmeyer_etf_options.pdf)
- 0DTE 时代（2022 以后）：Dim, Eraker & Vilkov "0DTEs: Trading, Gamma Risk and Volatility Propagation"（样本 2016-09 至 2026-02-02 的更新版）：**做市商正 gamma 倾向产生日内反转，负 gamma 产生动量**；做市商净 gamma 平均为正，且与未来日内波动负相关 — [SSRN](https://papers.ssrn.com/sol3/Delivery.cfm/4692190.pdf?abstractid=4692190)；[ResearchGate](https://www.researchgate.net/publication/377984312_0DTEs_Trading_Gamma_Risk_and_Volatility_Propagation)
- Adams 等 "Do S&P 500 Options Increase Market Volatility? Evidence from 0DTEs"：dealer 在到期日全程维持正净 gamma，**更高净 gamma 预测 E-mini 订单流更强的反转**；0DTE 交易与实现波动负相关 — [论文 PDF](https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf)；[Quantpedia 摘要](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)
- 反方：Brogaard, Han & Won（仅二手）称 0DTE 交易一个标准差上升对应波动高约 9.1%，归因于散户投机而非 dealer 对冲；Cboe 估计 2023 年 dealer 净 0DTE gamma 仅占 S&P 期货流动性 0.04%–0.17%；2023-12-20 尾盘急跌 JPMorgan 归咎 0DTE、Cboe 则称当日 dealer 多为 long gamma — [Way of the Trader 摘要](https://wayofthetrader.com/education/futures/0dte-options-nq)；Princeton 论文认为证据不支持 gamma 反馈为主因 — [Princeton Thesis](https://theses-dissertations.princeton.edu/entities/publication/61115cd1-cb09-4a8b-9230-ff488fc2a386)
- 实践过滤器：QuantRocket 的 first-last 教程在 **VIX < 20 时禁用**该策略，理由是策略在高波动状态表现最好（实践改编，非论文结论）— [QuantRocket 教程](https://docs-2-0--quantrocket.netlify.app/codeload/first-last/first_last/Introduction.ipynb.html)
- Zarattini, Aziz & Barbon "Beat the Market: An Effective Intraday Momentum Strategy for SPY"（SSRN 4824172；noise area = 过去 14 日每个时刻相对开盘价的平均绝对偏离，突破即入场、收盘平仓）：头条 2007–2024 年化 19.6%、Sharpe 1.33；另一版本表格为总收益 178%、年化 6.2%、波动 10.9%、Sharpe 0.61（规格不同，未能核对对应关系）。第三方书评称作者检验了 VIX 分段稳健性，**策略在 VIX > 20 时表现更好，但关系非线性** — [Concretum](https://concretumgroup.com/beat-the-market-an-effective-intraday-momentum-strategy-for-sp500-etf-spy/)；[St. Gallen 版本](https://alexandria.unisg.ch/bitstreams/a99aba00-f967-49b3-aceb-f544dc386e0b/download)；[QuantMacro 书评](https://quantmacro.substack.com/p/paper-review-an-effective-intraday)
- **发表后衰减**：Paz 的独立复现在 2015–2024 样本内 Sharpe 1.34（复现成功），但 **2024-05 至 2026-03 样本外总收益仅 9.4%（买入持有 29.5%）、Sharpe 0.39**，作者称下降在统计上显著 — [SSRN（Paz）](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7290621)；[GitHub 复现](https://github.com/PazSheimy/spy-intraday-momentum-oos)；[Larry Swedroe 评论](https://larryswedroe.substack.com/p/when-beat-the-market-meets-the-real)
- Nasdaq 期货上的同类测试（2010–2017 定参，2018 起样本外）：做多端稳健（9 个 OOS 年中 6 年为正），**做空端样本内即为负**（"short is a mirage"）【单一博客】— [EdgeLab](https://edgelabtrading.com/blog/zarattini-intraday-momentum-nasdaq/)

### Inferences
- 用户自有结果（"跟随单向首 30 分钟" OOS Sharpe ≈ 0.86；"淡化早盘上涨"在 down/VIX 15-20 亏损）与 Gao et al.、Baltussen et al.、Zarattini et al. 的方向完全一致：在非低波动状态下，早盘方向倾向延续而非回归。用户的"high efficiency"过滤（单向推进）实质上筛出了"信息驱动/对冲需求同向"的日子，这与"宏观新闻日更强"的发现吻合。
- VIX 18.7 + contango（VIX/VIX3M ≈ 0.93）≈ "中等波动、无压力"。按文献，这是日内动量有效但非最强的区间；**最有价值的附加条件变量是 dealer gamma 符号（GEX）**：正 gamma 日倾向回归/区间，负 gamma 日倾向延续。建议把 GEX（或其代理：SPX 价格相对 gamma flip 水平）作为第二过滤器检验，而不是单纯依赖 VIX 阈值。
- 关于做空端：Nasdaq 测试中做空端失效，但那是长期牛市样本；在 below-50DMA 状态下做空端是否改善，没有找到直接证据——需在自有数据中按趋势状态分别统计多/空两侧。
- 衰减风险真实存在（Beat the Market 发表后 OOS Sharpe 骤降），用户 0.86 的 OOS Sharpe 若主要来自 2020/2022 等高波动年份，在中等波动期可能显著偏低——应按年份/VIX 桶拆分自有 OOS 结果。

### Gaps
- **没有找到任何按趋势状态（高于/低于 50/200 日均线）拆分日内动量的学术或实践研究。**
- Gao et al. 衰退期/高波动日系数、Baltussen 正/负 gamma 下的具体 R²，因 nd.edu 全文被拦截未能读取。
- 未找到 2015–2026 年 Gao 式首-末半小时规则的独立样本外复现（只找到 Zarattini noise-area 版本的 OOS）。

---

## Q3. 低于 50/200 日均线时的日频行为：自相关、熊市反弹、"sell the rip" vs "buy the dip"、波动聚集

### Takeaway
低于均线时最稳健的统计事实是**波动率显著上升（日均振幅约翻倍）且大涨日、大跌日都集中出现**（波动聚集），而非方向本身可预测；日频 mean reversion（RSI(2) 等 buy-the-dip）在均线下方依然存在但质量下降、在崩盘期失效。关于"均线下方日收益自相关更高"未找到正式检验；现有学术证据反而指向**波动冲击降低自相关（更多反转）**。未找到"低于 50DMA 且 5 日涨 3%"这一具体条件的可靠统计。

### Cited Findings
**波动与收益分布**
- 回测（自 1993 起）：S&P 500 在 200 日均线上方平均日内振幅约 1.05%，下方约 2.1%【出处待核：搜索摘要未指明是以下哪一页】— [Quantified Strategies 200DMA](https://www.quantifiedstrategies.com/200-day-moving-average/)；[TraderMarkus 76 年数据](https://tradermarkus.com/sp-500-200-day-moving-average/)
- 当指数位于**下行的 20 日或 50 日均线下方**时，年化波动率接近翻倍至约 30%【出处待核，疑为 Stockopedia】— [Stockopedia](https://www.stockopedia.com/content/the-sp-500-just-broke-below-its-moving-averages-heres-why-that-matters-1047835/)
- 1970 年起，200 日均线下方状态的年化波动 25.0%，对比买入持有 17.3%【出处待核】— [Jeroen Blokland](https://jeroenblokland.substack.com/p/transform-your-investment-strategy)；[TraderMarkus](https://tradermarkus.com/sp-500-200-day-moving-average/)
- 平均日收益：200DMA 上方 +0.09%/日，下方 -0.11%/日（样本期未注明）【弱】— [Sykon Capital](https://www.sykoncapital.com/article/what_happens_when_the_sp_500_index_falls_below_the_200_day_moving_average.)
- 12 个月前瞻收益：从 200DMA 下方出发均值 9.43% vs 上方 9.40%，中位数 13.0% vs 9.9%，但标准差 20.1 vs 13.8（下方分布更分散）【出处待核】— [Free Market Speculator](https://freemarketspeculator.substack.com/p/the-200-day-line-in-the-sand)
- Adam Grimes：均线存在清晰的分界——较短周期上是 mean-reversion 指标、到约 200 日才变成 trend-following 指标 — [Adam H Grimes](https://www.adamhgrimes.com/200-day-moving-average-work/)
- 跌破 50 日均线：过去十年 74 次，之后 6 个月上涨概率 81%、中位数 +8%（未条件化波动率）【单一来源】— [Stockopedia](https://www.stockopedia.com/content/the-sp-500-just-broke-below-its-moving-averages-heres-why-that-matters-1047835)

**熊市反弹 / 大涨日聚集**
- Hartford Funds（数据 1993–2022）：约 **78% 的最佳交易日出现在熊市中或牛市前两个月**；二手报道其 1996–2025 数据为 48% 在熊市、28% 在牛市前两个月、24% 在牛市其余时间 — [Hartford Funds](https://www.hartfordfunds.com/practice-management/client-conversations/managing-volatility/is-now-the-right-time-to-invest.html)；[Motley Fool 转述](https://www.fool.com/investing/2026/10/01/if-a-bear-market-is-coming-history-says-the-most/)
- StatOasis "Big Range Days"：大振幅日预测的是**波动而非方向**——次日振幅从"最平静日之后"的 0.715× 近期均值升至"最极端日之后"的 1.928×（2.7 倍差）— [StatOasis](https://statoasis.com/overfit/research/sp500-big-range-days)

**自相关 / 反转**
- "A Century of Market Reversals: Resurrecting Volatility"（ABFER 2024 会议论文）：日度市场自相关在负收益日更低；**波动冲击倾向降低收益自相关**（即更多反转）— [ABFER PDF](https://abfer.org/media/abfer-events-2024/annual-conference/papers-investment/AC24P3015-A-Century-of-Market-Reversals--Resurrecting-Volatility.pdf)
- Price Action Lab：SPY 252 日滚动 lag-1 自相关在 2020 年 3 月崩盘后跌至约 -0.40 以下，后回到约 -0.07【博客、滚动指标，非正式检验】— [Price Action Lab](https://www.priceactionlab.com/Blog/2021/09/mean-reversion-waning/)
- Ian Martin（期权隐含 6 个月自相关）：次贷危机前接近零，危机后为负 — [Journal of Financial Econometrics](https://academic.oup.com/jfec/article/19/1/39/6124729)
- 早期 SPDR 日度一阶自相关约 -0.0199、不显著（旧样本）— [Berkeley 论文](https://eml.berkeley.edu/~anderson/Sources-042212.pdf)
- 高频层面相反：日内超高频收益自相关在休市后和高波动时期倾向变为**正** — [CESA 工作论文](https://www.fernuni-hagen.de/igas/docs/cesa_wp_14.pdf)

**Buy the dip（RSI 类）在均线下方**
- Quantified Strategies RSI 阈值研究：去掉 200DMA 过滤后，RSI < 9 仍有约 357 笔交易、profit factor 2.15、最大回撤 14.6%；结论是"**200DMA 提升了质量，但并非 RSI 效应的全部来源**"；越超卖，短期 mean reversion 越强 — [Quantified Strategies Substack](https://quantifiedstrategies.substack.com/p/what-is-the-best-rsi-oversold-level)
- RSI(2)：2008 金融危机与 2020 年 3 月崩盘期间胜率跌破 60%，"buy the dip 反复失败"；建议用 VIX < 25 等过滤器 — [Quantified Strategies RSI 2](https://www.quantifiedstrategies.com/rsi-2-strategy/)
- 执行敏感性：某 SPY RSI(2) 变体改为次日开盘成交后收益从 +36.4% 降至 +19.4% — [SimpleMarkets](https://simplemarkets.io/strategies/index-etf-rsi2-dip)
- 50 日均线回踩（3% 区间）：未来 5 日平均超额收益小幅为正，但约 1/5 的触及在 5 日内收于区间下方、平均超额 -5.44%；边际持续约一周【单一作者】— [The Long Trend](https://thelongtrend.substack.com/p/how-to-trade-the-50-day-moving-average)

**当前位置**
- 某技术页（约 2026-11-10 至 11-13）：S&P 500 7,520.93，50 日 SMA 7,672.91，200 日 SMA 7,333.88，RSI(14) 44.5——即**低于 50 日、高于 200 日**（该页显示约 -2% 低于 50 日，与用户给出的 SPY -0.9% 不一致，可能是日期不同）【出处待核】— [Financhill](https://financhill.com/stock-price-chart/spx-technical-analysis)；[Investing.com](https://www.investing.com/indices/us-spx-500-technical)

### Inferences
- 当前是"**低于 50 日、仍高于 200 日**"的回调，而非 200 日下方的熊市。多数 buy-the-dip 统计（带 200DMA 过滤）恰好覆盖这一状态，历史上 1-5 日均值回归在此状态仍偏有利；但用户自有的日内结论（不要淡化早盘涨势）说明**日内与日频的最优方向逻辑可以不同**：日频偏 mean reversion，日内偏 momentum（与 Lou-Polk-Skouras 的"不同时段由不同 clientele 主导"一致）。
- 5 日 +3.3% 的反弹后 RSI 已离开超卖区，经典 RSI(2) 买点不再成立；"sell the rip"在 200 日上方的回调中缺乏稳健统计支持，在 200 日下方才更常被引用——本研究未找到支持在当前位置系统性做空反弹的量化证据。
- 由于波动聚集强（StatOasis 2.7 倍差、均线下方波动约翻倍），仓位应按 ATR/实现波动缩放，而不是固定手数；止损宽度需随 ATR 1.6% 放大。

### Gaps
- 未找到以 50/200 日均线状态为条件的**日度自相关或方差比（variance ratio）正式检验**。
- 未找到"低于 50DMA 时 5 日涨幅 ≥3%"后 1-5 日/20 日前瞻收益的可靠统计（建议自行回测）。
- 多条波动/收益统计的具体出处页面因 WebFetch 被拦截无法核实。

---

## Q4. VIX 15-20 vs <15 vs >20：日内振幅、趋势日频率、开盘区间突破（ORB）、跳空行为

### Takeaway
VIX 与日内预期振幅的换算关系有明确依据（VIX/√252 或 /√365），但**按 VIX 分桶的日内振幅、趋势日频率、ORB 胜率、gap 回补率，几乎找不到严谨、方法公开的统计**——现有数字多来自厂商博客。方向性共识是：日内动量/ORB 类策略在低 VIX（<13-15）明显变差，在中高 VIX（约 16-25）最好；极高 VIX 时机会与反转风险同时放大。Gap 的关键变量是**大小而非方向**。

### Cited Findings
- 换算：Cboe 指出日度预期波动 = VIX / √365（亦有实践者用 √252，两者相差约 20%）；Cboe 文中某 2014 时段 S&P 500 平均日绝对变动约 1.24%，对应 VIX 略低于 24 — [Cboe Insights](https://www.cboe.com/insights/posts/inside-volatility-trading-breaking-down-the-vix-index-and-its-correlation-to-the-s-p-500-index/)
- 正态分布下平均绝对变动 ≈ 0.80 × 标准差（用于把隐含波动换算成"平均日绝对涨跌"）— [GitHub options-event-risk](https://github.com/unaifmm/options-event-risk)
- VIX 系统性高于实现波动：StatOasis（1993–2026）显示 VIX 在 83.2% 的 SPY 交易日高于随后 21 日实际波动；自 1993 年 VIX 中位数约 17.67；首次 VIX 收盘 >31 后从次日开盘起算，SPY 下一个月平均 +2.83%（全样本 +0.82%）— [StatOasis VIX](https://statoasis.com/overfit/research/what-is-the-vix-index-a-beginner-s-guide-to-market-volatility)
- ORB 与 VIX（厂商/博客）：VIX 16–24 时 ORB 胜率约 58%，VIX < 13 时约 48%；另一来源称 VIX 16–25 胜率与盈亏比最佳；VIX 30+ 时 ES 15 分钟开盘区间可超 40 点，突破更猛但反转风险也更大；有来源明确警告叠加 VIX/星期/gap/宽度等多重过滤易过拟合【弱：厂商、方法不明，搜索摘要未指明每个数字的具体页面】— [PickMyTrade](https://blog.pickmytrade.io/opening-range-breakout-automation-for-prop-firms-2026/)；[SatoTrades](https://satotrades.com/guides/opening-range-breakout)；[Volatility Box](https://volatilitybox.com/research/opening-range-volatility-breakout)
- Zarattini & Aziz (2023, SSRN 4416622) "Can Day Trading Really Be Profitable?"：QQQ 5 分钟 ORB（9:35 入场、以开盘区间为止损），2016-01 至 2023-02，样本含两次熊市；头条称 QQQ 净增长 +675%（依赖杠杆，胜率低、靠少数大赢家）。独立复现：**滑点约 2.2¢/股即盈亏平衡**；NQ 确认过滤器单笔显著（t = 2.05），但**其 76% 的 PnL 来自 2022 年一年** — [论文 PDF](https://static1.squarespace.com/static/5983d931579fb366729580d8/t/643ed6765176b45506e41a01/1681839734183/SSRN-id4416622.pdf)；[GitHub 复现（giovannibrusco）](https://github.com/giovannibrusco/zarattini-2023-orb-qqq)；[Danfin 综述](https://danfin.net/opening-range-breakout-research)
- Gap（自 1993 起 8,397 个 S&P 500 开盘跳空）：方向是噪音、**大小才是信号**；"任意时间回到前收盘"口径下下跳空回补 98%、上跳空 94%，中位数同日回补；>2% 的跳空回补 83%，通常在 2 日内 — [StatOasis Gaps](https://statoasis.com/overfit/research/sp500-opening-gaps)
- 另一口径：1993 年以来 1–2% 的上跳空**同日**回补仅约 26%，5 个交易日内 53%（291 例）；0–0.19% 小跳空回补 87%（上）/92%（下），0.2–0.39% 降至 53%/69%【出处待核：摘要未指明来自以下哪一页】— [Trade That Swing](https://tradethatswing.com/sp-500-spy-es-gap-fill-strategy-and-statistics/)；[thetrading.tools Gap Analysis](https://www.thetrading.tools/gap-analysis)
- 唯一按 VIX 条件化的 gap 统计：SPY Suite 称高 VIX 状态 gap-up 成功率最佳（62.5%），分段为 VIX <17 / 17–25 / >25【弱：无方法、无样本量】— [SPY Suite](https://spy-suite.vercel.app/)
- Shareplanner 对 SPY/QQQ 大幅隔夜跳空在日内如何演化的讨论（"fading the gap"）— [Shareplanner](https://www.shareplanner.com/blog/strategies-for-trading/fading-the-gap-how-large-overnight-moves-in-spy-and-qqq-play-out-during-the-trading-day.html)

### Inferences
- 以 VIX 18.7 计：VIX/√252 ≈ 1.18%（年化转日度 1σ），VIX/√365 ≈ 0.98%；乘 0.8 得"隐含平均日绝对收益"约 0.8%–0.95%。用户的 ATR 1.6% 是高低振幅（含跳空），本就应大于 close-to-close 波动，所以两者并不矛盾；但若 ATR/隐含日 σ 比值明显高于历史常态，说明实现振幅相对隐含偏高——这类环境对日内突破/动量较友好（此为推断，未找到直接统计）。
- 在 VIX 15-20 区间，厂商数据与 Zarattini 书评都暗示 ORB/动量"可用但不是最佳"；而 ORB 复现中 76% PnL 集中在 2022 年，提示**此类策略的收益高度集中于少数高波动年份**，中等波动期期望值应打折。
- Gap：当前状态下应把 gap 大小（以 ATR 归一）作为主要条件，而非方向；小 gap（<0.2%）回补概率高、大 gap 同日回补概率低——与用户"不要淡化早盘走势"的发现一致（大 gap + 单向首 30 分钟 → 延续）。

### Gaps
- **未找到可靠的"按 VIX 分桶（<15 / 15-20 / >20）的 SPY 平均日内振幅、趋势日频率"统计**；"趋势日"缺乏标准定义。
- 未找到同行评审的 VIX 条件化 ORB 或 gap 回补研究；所有 VIX 分段数字均为厂商/博客级。
- 建议用自有 1 分钟数据直接计算：各 VIX 桶的 (high-low)/open、|close-open|/(high-low)（efficiency）分布、ORB 胜率、gap 同日回补率。

---

## Q5. 事件/宏观背景：鹰派状态下通胀数据日与 Fed 讲话日的指数日内行为，以及巨型股单股冲击（指数集中度效应）

### Takeaway
在 2022 式鹰派/高通胀状态下，CPI 日 SPY 平均绝对波动约为普通日的 1.7 倍，且**实际波动超过期权隐含（1.48×）**；2023 年以后 CPI 日实际波动反而低于隐含（0.78×）。Gao et al. 发现宏观新闻日日内动量更强，2022 年 Jackson Hole 等鹰派讲话日呈"先震荡、后单边"的形态。巨型股单股冲击（DeepSeek 日 NVDA -17%、本周 NVDA CEO 离职）对指数的冲击远小于单股，并伴随板块轮动与单股日内大幅反转；本周指数已在 NVDA 事件当日收复跌幅。

### Cited Findings
**CPI 日**
- 2022 年 SPY 在 CPI 日平均绝对变动 1.94%，其他日 1.16%；2022-09-13 CPI 日 -4.3%、2022-11-10 +5.5%；全样本（2016-06 至 2026-09，120 次）CPI 日 0.79% vs 其他日 0.73%（差异小）— [YX Insights](https://www.yxinsights.com/p/what-is-cpi)
- 另一研究（2018-09 至 2026-01，87 次）：CPI 日 0.86% vs 其他日 0.68%；**2022–2023 加息周期 CPI 日 1.49% vs 0.98%** — [Weekly Catalysts "CPI Day Was Just a Tuesday"](https://weeklycatalysts.substack.com/p/cpi-day-was-just-a-tuesday)
- 期权隐含：2022 年 CPI 日实际波动为隐含的 **1.48 倍**；**2023 年以来仅 0.78 倍（95% CI 0.60–0.96）**，即近年 CPI 期权被高估（样本 2022-05 至 2026 年末）— [GitHub options-event-risk](https://github.com/unaifmm/options-event-risk)
- ORATS WHAM：某次 7 月 CPI 日隐含约 ±56 SPX 点，正常日约 ±31 点（约 1.79×）— [ORATS WHAM](https://orats.com/wham)
- Russell Rhoads 对 CPI 与 FOMC 前后指数及期权价格的历史整理 — [ListDer Research](https://russellrhoads.substack.com/p/index-option-history-around-cpi-reports)；[CPI 周二 / FOMC 周三](https://russellrhoads.substack.com/p/historical-index-and-option-price)
- 当前：2026-11-11 有报道称 S&P 500 因 CPI 偏热下跌 — [Trefis](https://www.trefis.com/stock/spy/articles/624200/s-p-500-down-on-hot-cpi-sell-or-hold/2026-11-11)；2026-11-12 评论"鹰派 Fed 遇上股市急涨"— [BabyPips](https://babypips.com/analysis/headline-hawkish-fed-stock-market-surge-rallies-last-2026-11-12)
- Gao et al.：日内动量在重大宏观新闻发布日更强（见 Q2）— [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2440866)

**Fed 讲话日**
- Neuhierl & Weber (2019, JME)：由不同期限联邦基金期货变化构建的"slope 因子"在**周频**预测股票收益（更快宽松 → 正收益）；主席/副主席讲话语气与 slope 因子相关，**更鹰派的语气预测更快紧缩**；预测力集中于高不确定性时期 — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304393219301400)；[NBER WP](https://www.nber.org/system/files/working_papers/w22831/w22831.pdf)
- JFE 2021 "Real-time price discovery via verbal communication: Fedspeak"：股价对 Fed 主席关于货币政策问题的回答特别敏感 — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X21005109)
- 牛津论文研究央行讲话的市场反应（日内反应被作为独立问题处理）— [Oxford ORA](https://ora.ox.ac.uk/objects/uuid:9882827b-3117-4f75-a1f7-749e1abc2940/files/rx059c899b)
- 2022-08-26 Powell Jackson Hole：S&P 500 跌约 3.4%（为 6 月中以来最大单日跌幅）；AP 描述讲话期间先震荡、一度几乎收复跌幅，随后**决定性走低**，仅 5 只成分股收红（3.4% 应为收盘跌幅而非日内低点）— [NPR Illinois](https://www.nprillinois.org/2022-08-26/jerome-powell-says-fed-is-resolved-to-fight-inflation-even-if-it-brings-economic-pain)；[MarketBeat](https://www.marketbeat.com/articles/sp-500-drops-3-after-fed-chief-says-more-rate-hikes-coming-2022-08-26)；[ThinkAdvisor](https://www.thinkadvisor.com/2022/08/26/stocks-tumble-as-powell-throws-cold-water-on-pivot/)

**巨型股单股冲击**
- 2025-01-27 DeepSeek：NVDA 开盘后一度跌约 13%，收盘约 -17%，市值损失约 5,890 亿美元（单股史上最大）；S&P 500 收 -1.46%（盘中报道 -1.86%），Nasdaq 约 -3%，**Dow 当日反弹**；报道把指数下跌归因于 NVDA 在主要指数中的权重；Truist 称科技约占 S&P 500 的 45% — [Bloomberg](https://www.bloomberg.com/news/newsletters/2025-01-27/nvidia-loses-589-billion-as-deepseek-batters-stock-evening-briefing-americas)；[CNBC](https://www.cnbc.com/2025/01/26/stock-market-news-for-jan-26-2025.html)；[Yahoo Finance](https://finance.yahoo.com/news/live/stock-market-today-nasdaq-clobbered-nvidia-sinks-17-while-dow-stages-comeback-as-ai-fears-shake-markets-210101592.html)；[CNN](https://www.cnn.com/2025/01/27/tech/deepseek-stocks-ai-china)；[Business Standard](https://www.business-standard.com/amp/world-news/nvidia-s-465-bn-plunge-triggered-by-deepseek-largest-in-market-history-125012701354_1.html)
- 2026-11-12 Jensen Huang 辞任 NVDA CEO（CFO Colette Kress 任临时 CEO）：NVDA **早盘跌超 13%，收盘仅 -4.34%**（市值蒸发约 1,820 亿美元）；**主要美股指数周四收高，收复早盘部分由此引发的跌幅**；Bernstein 将目标价从 400 砍半至 200 — [CNBC 收盘](https://www.cnbc.com/2026/11/12/nvidia-nvda-jensen-huang-second-affair.html)；[CNBC 直播](https://www.cnbc.com/2026/11/12/nvidia-jensen-huang-ceo-live-updates.html)；[CNBC 分析师观点](https://www.cnbc.com/2026/11/12/jensen-huang-nvidia-affair-ceo.html)；[CNN](https://www.cnn.com/2026/11/11/business/live-news/nvidia-jensen-huang-investigation-fallout)
- 次日（11-13）期货上涨、"华尔街翻篇"；NVDA 反弹约 5.8%–6%【后者为弱来源】— [ZeroHedge](https://www.zerohedge.com/markets/futures-rise-wall-street-moves-jensen-microsoft-outage-drags-day-two)；[CryptoBriefing（弱）](https://cryptobriefing.com/nvidia-stock-rebounds-6-after-jensen-huangs-resignation/)

### Inferences
- 鹰派 + 黏性通胀的宏观组合更接近 2022–2023（CPI 日实际 > 隐含、平均绝对波动 ~1.5–1.9%）而非 2023 年后（实际 < 隐含）。若通胀数据重新成为主导变量，**"卖 CPI 日跨式"这一 2023 年后有效的做法可能失效**，而"CPI/讲话日跟随首 30 分钟方向"更契合 Gao et al. 的宏观新闻日发现与用户自有规则（推断，需要自有数据按事件日分组验证）。
- Fed 讲话日（尤其主席讲话）的典型形态是"讲话中震荡、消化后单边"——这意味着首 30 分钟规则在**讲话时间不在开盘时**的日子里可能信号错位；更合理的是以讲话结束后的首个 30 分钟作为"opening range"（推断）。
- 巨型股冲击：两次 NVDA 事件都显示**单股早盘深跌后大幅收复（-13% → -4.34%；DeepSeek 日则延续至 -17%）**，而指数跌幅远小于单股、且有资金轮动到非科技（Dow 反弹）。对 SPY 日内策略的含义：单股冲击日的指数首 30 分钟方向可能被单一权重股"污染"，efficiency 过滤器应同时检查等权/广度（如 RSP 或 advance-decline）是否同向；若指数下跌主要由单股贡献而广度不弱，延续概率可能偏低（推断，未找到直接研究）。
- 当前 +3.3% 的 5 日反弹 + 事件后指数"翻篇"，更像是波动正在回落、dealer 可能回到正 gamma 的阶段——这会削弱日内动量、利好区间/回归（依据 Dim-Eraker-Vilkov 与 Adams 等的 gamma 结论，属推断）。

### Gaps
- 未找到 2022 年 CPI 日**纯日内（open-to-close 或按分钟）**的平均振幅/方向延续统计；上述数字多为 close-to-close。
- 未找到"Fed 官员（非主席）讲话日"的日内事件窗口研究。
- 未找到以 cap-weight vs equal-weight 对比巨型股冲击日的系统性研究，也未找到 2026-11-12 当日 S&P 500 的精确涨跌幅。
- 本周 NVDA 事件为训练截止后的新事件，仅基于新闻报道，后续发展（国会作证等）可能改变冲击性质。

# Dealer Gamma Exposure (GEX) 与 SPX/SPY 日内均值回归 vs 趋势：证据、规则与可用数据

> 研究背景：我们在 SPY 上做开盘一小时 fade（跳空低开 + 反弹失败后做空 / 买 0DTE put），2019-2026 回测 Sharpe 约为 0，用价格/成交量/VIX/趋势无法区分赢家和输家。本笔记评估"dealer gamma 体制（正 gamma → 均值回归，负 gamma → 趋势）"能否作为过滤变量，以及有哪些可回测的数据。
>
> 研究方式说明：本次沙盒中 WebFetch 对 squeezemetrics.com、alphaarchitect.com 等域名被网络白名单拦截（curl 下载 `squeezemetrics.com/monitor/static/DIX.csv` 也被代理 403 拒绝），因此几乎全部依赖 WebSearch 摘要。凡是来自二手摘要、未能对照原文核实的数字，都已标注"二手/未核实"。证据等级标注：【同行评审】、【工作论文】、【交易所研究】（Cboe 有商业利益）、【供应商/营销】、【博客/论坛】。

## 1. 学术文献怎么说：dealer gamma 与日内动量/反转、波动、pinning

### Takeaway
同行评审与工作论文的主线结论方向一致：dealer 净 gamma 为负时，对冲交易顺势，指数日内呈动量（尤其是收盘前半小时）；净 gamma 为正时，对冲交易逆势，波动更低、反转更强。但证据主要集中在"收盘前最后半小时动量"和"未来波动率"两个维度，**专门针对开盘第一小时 fade 的证据基本没有**，且正 gamma 下"反转可交易"的证据比负 gamma 下"动量存在"的证据弱。

### Cited Findings

**核心论文：Baltussen, Da, Lammers & Martens (2021)【同行评审，JFE】**
- 发表于 *Journal of Financial Economics* 142(1), 2021, pp. 377-403 — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)；工作论文版 [SSRN 3760365](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)，PDF [academicweb.nd.edu](https://academicweb.nd.edu/~zda/intramom.pdf)
- 用 1974-2020 年 60 多个期货（股指、债券、商品、外汇）的日内数据，发现所有资产类别都存在"当日前段收益预测最后半小时收益"的日内动量 — [Tinbergen](https://tinbergen.nl/publication/168044/hedging-demand-and-market-intraday-momentum)；[SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)
- 机制：期权做市商（以及杠杆/反向 ETF 收盘再平衡）的 gamma 对冲需求。做市商负 gamma 时必须与标的价格同向交易，负得越多交易越激进，从而制造动量 — [nd.edu PDF](https://academicweb.nd.edu/~zda/intramom.pdf)
- 原文摘要措辞："Using a direct proxy of their negative gamma exposure (NGE), we confirm that market intraday momentum is present for the index when NGE is negative and becomes stronger when NGE becomes more negative." — [nd.edu PDF](https://academicweb.nd.edu/~zda/intramom.pdf)；[ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X21001598)
- NGE 由 S&P 500 指数期权自 1996 年 1 月起的数据构建（结束时间在摘要中被截断）— [nd.edu PDF](https://academicweb.nd.edu/~zda/intramom.pdf)
- 二手/未核实：有二手总结称"正 gamma 日无显著日内动量"，以及负 gamma 日回归系数 6.63、t=4.78；以上未能对照原表核实 — [VolArchitect Substack](https://dn12448583.substack.com/p/when-positive-gamma-fails)；[Tinbergen 搜索摘要](https://tinbergen.nl/publication/168044/hedging-demand-and-market-intraday-momentum)

**Gao, Han, Li & Zhou (2018) "Market intraday momentum"【同行评审，JFE】——与我们的开盘 fade 直接相关**
- *Journal of Financial Economics* 129(2), 2018, pp. 394-414 — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)
- 用 1993-2013 年 S&P 500 ETF（SPY）高频数据：第一个半小时收益（从前一日收盘算起，因此包含隔夜跳空）预测最后半小时收益 — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414)；[WUSTL](https://profiles.wustl.edu/en/publications/market-intraday-momentum/)
- 工作论文版：样本内预测 R² 1.6%，样本外 1.2%；**当第一个半小时收益为正时效应更强** — [工作论文 PDF](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)；[Alpha Architect 2014](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)
- 独立复制（CXO Advisory，2012-08 至 2014-05）：首半小时为正时持有 SPY 最后半小时，年化毛收益 6.3%，对比全部最后半小时持有为 -0.5% — [CXO Advisory](https://cxoadvisory.com/calendar-effects/first-and-last-half-hours-of-trading-linked)

**Barbon & Buraschi "Gamma Fragility"【工作论文，SSRN】**
- 用大量指数和个股期权构建总体 gamma imbalance 代理；负 gamma imbalance 对应日内动量，正 imbalance 对应日内反转，效应依赖市场流动性，集中于最不流动的股票 — [SSRN 3725454](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3725454)；[Google Books 摘要](https://books.google.com/books/about/Gamma_Fragility.html?id=bn0izgEACAAJ)；[St. Gallen 全文](https://www.alexandria.unisg.ch/bitstreams/25fec636-90a2-4735-a3a4-dfc0b68d3feb/download)
- 作者将其定位为区别于信息摩擦和融资流动性摩擦的"delta 对冲反馈"渠道；gamma imbalance 与闪崩事件的频率和幅度相关 — [SSRN 3725454](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3725454)
- 机制表述：gamma imbalance 为正时 dealer 必须"卖出上涨"，其订单流是逆向力量，从而产生日内均值回归 — [BSIC 解读](https://bsic.it/how-dealers-gamma-impacts-underlying-stocks/)
- 二手/未核实：有 Substack 称每 1% 价格变动对应约 5-25 bp 的收益延续（视设定而定），未核实 — [Gabriel Michaels Substack](https://gabrielmichaels.substack.com/p/the-mechanical-market-the-jpm-collar)

**Ni, Pearson, Poteshman & White (2021)【同行评审，RFS】与 Ni, Pearson & Poteshman (2005) pinning**
- 标题实为 "Does Option Trading Have a Pervasive Impact on Underlying Stock Prices?"，*Review of Financial Studies* 34(4), 2021, pp. 1952-1986 — [Illinois Experts](https://experts.illinois.edu/en/publications/does-option-trading-have-a-pervasive-impact-on-underlying-stock-p/)；[IDEAS](https://ideas.repec.org/a/oup/rfinst/v34y2021i4p1952-1986..html)
- 核心结论（据二手引用）：可能做 delta 对冲者的净期权头寸 gamma 与标的股票绝对收益（波动）负相关；样本主要是个股期权 — [OU 工作论文 PDF](https://www.ou.edu/dam/price/Finance/CFS/paper/pdf/pearsonPoteshmanWhite.pdf)；[Cboe 托管论文对其的引用](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)
- 2005 年 JFE 论文：delta 对冲导致个股在期权到期日向行权价聚集（pinning）— [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0304405X05000577)
- 有引用文献指出 2021 年论文的机制是"gamma→波动"，并不意味着 pinning — [NTU 会议版](http://web.nbs.ntu.edu.sg/general/NTUFinanceConference2019/downloadpapers/paperfolder/FC2019D2_OptionTrading.pdf)

**0DTE 时代的 SPX 证据【工作论文 / 交易所研究】**
- Dim, Eraker & Vilkov "0DTEs: Trading, Gamma Risk and Volatility Propagation"：做市商 0DTE 库存净 gamma 平均为正，且与未来日内波动负相关；**做市商正（负）库存 gamma 强化日内价格反转（动量）**；未发现 0DTE 未平仓 gamma 传播或无条件放大指数波动 — [SSRN 4692190](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190)；[WFA 版本](https://westernfinance-portal.org/viewpaper?n=950096)；[ResearchGate](https://www.researchgate.net/publication/377984312_0DTEs_Trading_Gamma_Risk_and_Volatility_Propagation)
- 注意：该论文早期版本曾主张 0DTE 卖方主导的对冲流会"加剧"市场波动，结论在不同版本间有变化 — [Cboe 托管论文](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)（搜索摘要）
- Adams, Fontaine & Ornthanalai：有 0DTE 可交易的日子市场波动更低；净 gamma 变化预测未来约 10 分钟 S&P 500 波动降低，效应约一小时后消退 — [Fontaine 个人站 PDF](https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf)；[Quantpedia 总结](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)；SEC DERA 论文亦引用其"0DTE 交易与已实现方差下降相关" — [SEC DERA](https://www.sec.gov/files/dera-hope-reasonable-prc-2503.pdf)
- Cboe 托管的论文 "0DTE Index Options and Market Volatility: How Large is Their Impact?"：2023 年做市商 0DTE 净 gamma 仅占当日 S&P 500 期货流动性的 0.04%-0.17%；gamma 的典型影响是降低波动，平均降低约 0.2 个百分点 — [Cboe PDF](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)（据搜索摘要，未逐表核实；Cboe 作为 0DTE 产品方有利益关系）
- 反方：Brogaard, Han & Won 称 0DTE 交易量上升 1 个标准差对应波动高于均值 9.1%，主要归因于投机性散户（二手转述，未核实）— [Way of the Trader](https://wayofthetrader.com/education/futures/0dte-options-nq)

**其他相关研究**
- AFA 2024 工作论文 "Where does gamma hedge drive the intraday market move?"：来自看涨/看跌期权的空 gamma 头寸显著影响**当日后段**的日内动量；行权价高于标的价格的 gamma 头寸对日内动量无影响（仅见片段）— [AFA](https://afajof.org/management/viewp.php?n=129472)
- Buis, Pieterse-Bloem, Verschoor & Zwinkels (2024) "Gamma positioning and market quality"【同行评审，JEDC 164:104880，但为**模拟研究**】：动态对冲者净 gamma 上升降低波动、提高稳定性；负 gamma 提高波动、使市场更易失灵 — [IDEAS](https://ideas.repec.org/a/eee/dyncon/v164y2024ics0165188924000721.html)；[EUR PDF](https://pure.eur.nl/files/149733755/1-s2.0-S0165188924000721-main.pdf)；[VU](https://research.vu.nl/en/publications/gamma-positioning-and-market-quality/)
- Anderegg, Ulmann & Sornette (2022)【同行评审，JIMF 124】：研究对象是**外汇市场而非 S&P 500**；delta 对冲者订单流使 EUR/USD（USD/JPY）年化波动提高 0.7%（0.9%）— [IDEAS](https://ideas.repec.org/a/eee/jimfin/v124y2022ics0261560622000304.html)；[ResearchGate](https://www.researchgate.net/publication/358837574_The_Impact_of_Option_Hedging_on_the_Spot_Market_Volatility)
- 中国 SSE 50 ETF 期权的样本外检验支持对冲假说（摘要措辞为 "net gamma positions" 日动量更显著，正负号表述在摘要中不清晰）— [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0378437122003624)
- Park & Zhao "Inelastic Hedging Demand and Intraday Momentum"：金融中介的非弹性对冲需求放大日内动量 — [NFA](https://portal.northernfinanceassociation.org/viewp.php?n=2240183764)
- 个股横截面的收盘动量与期权对冲 — [EFMA 2021](https://www.efmaefm.org/0EFMAMEETINGS/EFMA%20ANNUAL%20MEETINGS/2021-Leeds/papers/EFMA%202021_stage-2049_question-Full%20Paper_id-237.pdf)；Da 等的 EOD 研究 — [nd.edu EOD.pdf](https://www3.nd.edu/~zda/EOD.pdf)

### Inferences
- 我们的现象（"fade 早盘上涨平均亏钱"）与 Gao et al. (2018) 的日内动量完全一致：首半小时（含隔夜跳空）为正时，后续倾向延续而非回归，而且该效应在首半小时为正时更强。这意味着"无条件 fade 早盘反弹"本身就是在逆一个有文献支持的效应交易，Sharpe≈0 甚至为负并不意外。
- 理论上，若 Baltussen/Barbon-Buraschi/Dim-Eraker-Vilkov 的结论成立，"只在正 gamma 时 fade"的逻辑方向是对的：正 gamma 下动量减弱/反转增强。但文献主要检验的是"负 gamma → 动量存在"，而"正 gamma → 足以产生可交易反转"的直接证据较弱（Baltussen 的二手总结只说正 gamma 日"无显著动量"，即"不延续"不等于"会反转"）。
- 时间窗错配：现有指数级证据集中于收盘前最后半小时（与对冲再平衡、杠杆 ETF 集中在尾盘有关），AFA 2024 论文也指向"当日后段"。开盘一小时的 gamma 效应缺乏直接研究，而且开盘时用的 OI 是前一日结算值，0DTE 新开仓尚未计入。
- 跳空低开日往往伴随 put 需求上升和价格下跌，按标准 GEX 假设此时 GEX 更容易偏低或为负，因此"仅正 gamma 才做"这一过滤可能会过滤掉我们大部分的跳空低开样本，样本量风险很大。
- 出版偏差：方向一致的结论来自多篇论文，但作者之间存在互相引用和共享数据（OptionMetrics/Cboe Open-Close）的情况；Dim-Eraker-Vilkov 结论在版本间翻转，说明结论对设定敏感。

### Gaps
- 未能取得 Baltussen et al. 原文表格，无法核实"正 gamma 日无显著动量"、系数大小及 NGE 的确切构造（使用 OptionMetrics 还是 Cboe Open-Close 数据未能确认）。
- 未找到任何同行评审论文直接检验"净 dealer gamma 与 SPX 开盘时段收益自相关"或"跳空后首小时反转"的关系。
- 未找到 Federal Reserve 或 BIS 关于 0DTE / dealer gamma 对冲的一手报告（搜索仅得到二手转述的 BIS 对 2024-08-05 VIX 飙升的分析，未能核实）。
- Barbon & Buraschi 对 SPX 指数层面（而非个股）的具体效应大小未能核实。

## 2. SqueezeMetrics GEX 与 DIX：定义、免费历史 CSV、方法学局限

### Takeaway
SqueezeMetrics 提供最长的免费 GEX 日频历史（GEX 自 2004 年起，DIX 自 2010/2011 年起），是做"体制过滤"回测最便宜的起点；但它是**日频、按收盘计算**的估计量，核心依赖"客户净卖出 call、净买入 put（即 dealer 多 call 空 put）"这一假设，SqueezeMetrics 自己在 2020 年承认原版 GEX 在某些市场下不能产生合适的预测，并改为考虑交易方向和 vanna 的 GEX 2.0 / GEX+。

### Cited Findings

**定义与白皮书**
- 白皮书 "Gamma Exposure" 日期为 2016 年 3 月，2017 年 12 月修订，2019 年 1 月公开 — [SqueezeMetrics X 推文](https://x.com/squeezemetrics/status/1085648131893518337?lang=en)；[白皮书 PDF](https://squeezemetrics.com/monitor/download/pdf/white_paper.pdf)
- 白皮书核心图：前一日 GEX vs 次日 SPX 收益分布，"GEX 跌破零时波动率呈指数式上升，GEX 上升时收益分布逐渐收窄"；白皮书还称筛选 GEX 接近零的成分股获得超额收益（数字在摘要中被截断）— [白皮书 PDF](https://squeezemetrics.com/monitor/download/pdf/white_paper.pdf)；[镜像 PDF](https://optionsoffice.ru/wp-content/uploads/2019/11/Gamma-exposure.pdf)
- 符号约定：原版 GEX 假设客户净卖出 call（备兑）、净买入 put（保护性），即 dealer 多 call、空 put；GEX 的正负号取决于这一假设 — [LuxAlgo](https://www.luxalgo.com/library/concept/gamma-exposure/)；[Alphanume](https://www.alphanume.com/blog/what-is-dealer-gamma-exposure-gex)
- SqueezeMetrics 自己的定位：GEX 是"对波动的潜在压力的估计，不是对市场方向的预测" — [Wizard of Ops 引述](https://www.wizofops.com/articles/why-not-gex)（搜索摘要）
- SqueezeMetrics 2020-03-15 周报承认"带有原始假设的 GEX 无法为这类市场产生合适的预测"，并转向同时考虑交易方向和 vanna 的 GEX 2.0 — [SqueezeMetrics notes 2020-03-15](https://notes.squeezemetrics.com/2020-03-15.pdf)
- 营销性质声明：SqueezeMetrics 推文称"当前 DIX 与 GEX 组合历史上对应平均 1 个月收益 +2.00%"（无方法细节，属营销）— [SqueezeMetrics X](https://x.com/SqueezeMetrics/status/1448405320057987072)

**免费历史数据文件**
- 官方数据指南（日期 2026-10-29）描述两个文件：**Chart.csv**（SPX 图表下载，2016 年至今，29 列，价格 K 线基于全收益指数 SPXTR）与 **GEX.csv**（较老的主表，2004 年至今，23 列，价格为普通 SPX）；两者均按交易日更新 — [SqueezeMetrics guide.pdf](https://squeezemetrics.com/monitor/static/guide.pdf)
- 指南称：重叠日期上 Chart.csv 的 GEX_PLUS 与 GEX.csv 的 GEX+ 一致；GEX+ 为"原始 GEX+ dealer 敞口，合并 GEX 与 VEX（vanna）敏感度"；DIX 在当前文件中自 2010-01-04 起；RISC/VIBE 自 2005 年起；DIX=45 表示 45% — [SqueezeMetrics guide.pdf](https://squeezemetrics.com/monitor/static/guide.pdf)
- **前视偏差警示**：文档称 DATE 指的是交易时段，"不保证每个字段在该交易日收盘时已可得"，并建议使用前先检查最新发布日期 — [SqueezeMetrics guide.pdf](https://squeezemetrics.com/monitor/static/guide.pdf)；[SqueezeMetrics docs](https://squeezemetrics.com/monitor/docs)
- 经典 DIX.csv（`squeezemetrics.com/monitor/static/DIX.csv`）：第三方 GitHub gist 显示其列为 `date, price, dix, gex`，样例行从 2011 年开始（price≈1361，dix≈0.38）；该 gist 非官方，未能确认是否就是当前 DIX.csv 的表头 — [GitHub gist](https://gist.github.com/jmhsi/2c6ba9356472412e9348d09f89f8d6e3?short_path=1ec6c22)；下载入口页 — [squeezemetrics.com/monitor/dix](https://squeezemetrics.com/monitor/dix)
- 第三方比较文章称 SqueezeMetrics 免费提供历史 CSV，但无免费实时 API — [FlashAlpha 比较文](https://flashalpha.com/articles/best-gex-api-2026-flashalpha-vs-spotgamma-vs-unusual-whales)（供应商，竞争对手）
- 社区 notebook 示例同时使用 SqueezeMetrics 与 SpotGamma 数据 — [Good Coder Bad Trader notebook](https://goodcoderbadtrader.com/gex-notebook)

**方法学批评**
- 实际仓位可能与假设背离：最明显的是大量 call 买入使 dealer 处于空 call 状态；buy-write、机构价差交易、指数复制都会混淆符号假设 — [LuxAlgo](https://www.luxalgo.com/library/concept/gamma-exposure/)；[Alphanume](https://www.alphanume.com/blog/what-is-dealer-gamma-exposure-gex)
- Wizard of Ops（Volland，供应商）认为 GEX 服务观察到的"磁吸效应"实际上是 vanna 效应，隐波动态主导时 GEX 水平未必如宣传般生效 — [Wizard of Ops](https://www.wizofops.com/articles/why-not-gex)
- 论坛用户对 SPX 的分析：GEX 与未来**带符号收益**无可见关系，但与未来波动有一定关系（r²≈0.15）；并认为白皮书纳入 GFC 时段有误导性【论坛，低可信】— [Elite Trader](https://www.elitetrader.com/et/threads/dealer-gamma-institutional-options-market-making.340500/page-5)
- Cboe（能看到真实成交方向）称 SPX 0DTE 做市商仓位"相当微小（fairly de minimis）" — 搜索摘要引自 [Cboe 0DTEs Decoded](https://www.cboe.com/insights/posts/0-dt-es-decoded-positioning-trends-and-market-impact)

### Inferences
- 对我们的回测而言，SqueezeMetrics GEX.csv（2004-）完整覆盖 2019-2026 样本，免费，可直接做"前一日 GEX 符号/分位数 → 当日开盘 fade 收益"的条件分析，是成本最低的第一步。
- 因为是日终值，且官方提醒 DATE 不保证收盘时可得，回测中**必须使用 t-1 日的 GEX 来过滤 t 日开盘交易**，不能用同日值。
- GEX（以及 GEX+ 中混入的 VEX）与 VIX 高度相关（见第 4 节回测），而我们已知 VIX 区分不了赢家/输家，所以 GEX 的增量信息可能有限，需要显式控制 VIX。
- 2020 年后 SqueezeMetrics 方法变化（GEX 2.0/GEX+）意味着序列可能存在方法断点，历史值是否回填重算未知，需在回测中检验结构断点。

### Gaps
- 由于网络被拦截，未能直接下载 DIX.csv / GEX.csv / Chart.csv 核实当前表头、起始日期和数值单位；GEX.csv 23 列和 Chart.csv 29 列的完整列名未能获取。
- 未确认 SqueezeMetrics 历史 GEX 是否在方法改版后被回填重算（这影响是否存在前视/再拟合偏差）。
- 未找到同行评审研究直接检验 SqueezeMetrics GEX 序列本身的预测力。

## 3. 其他数据源：SpotGamma、MenthorQ、Tier1Alpha、Cboe、Unusual Whales 等（免费 vs 付费、历史长度）

### Takeaway
除 SqueezeMetrics 外，可用于回测的现成 GEX 历史主要来自付费供应商：FinzData（日频，自 2010 年）、Unusual Whales（日频 GEX CSV，约 2019 年起；API 按套餐 1-2 年回看）、FlashAlpha（声称分钟级，起始年份两处说法冲突）。SpotGamma 的 Zero Gamma / Volatility Trigger 是专有模型输出，未找到可下载的历史档案。MenthorQ、Tier1Alpha 本次未找到可核实的历史数据信息。若要自建，原始 SPX 期权链历史可从 Cboe DataShop/Historical Option Data 等购买。

### Cited Findings

**SpotGamma（付费，营销性质为主）**
- Zero Gamma 是模型价格而非观测值：在一系列假设的现货价格上重算期权 gamma，找总 gamma 穿越零的位置；因依赖库存和定价假设，不同供应商公布的穿越点不同 — [SpotGamma GEX 指南](https://spotgamma.com/gamma-exposure-gex/)；[SpotGamma Zero Gamma 支持页](https://support.spotgamma.com/hc/en-us/articles/15297958613907-Zero-Gamma)
- Volatility Trigger 是 SpotGamma 专有水平，基于其估计的 gamma 分布而非普通零点；官方描述为"识别最后一个主要支撑位"，与标准零 gamma 水平"略有不同"；跌破只是"情境"而非"dealer 已翻转或波动必然扩张的证明" — [SpotGamma Volatility Trigger](https://spotgamma.com/volatility-trigger-zero-gamma-trading/)；[SpotGamma Key Levels](https://spotgamma.com/options-key-levels-explained/)
- 搜索未发现 SpotGamma 公开的历史 Volatility Trigger / Zero Gamma 档案或可下载数据 — 同上搜索结果

**Unusual Whales（付费，价格低）**
- API 有按日期参数化的 GEX levels 端点（call wall、put wall、gamma flip、gamma magnet），可选基于成交量（当日方向化流量）或基于 OI 的敞口口径 — [Unusual Whales API 文档](https://api.unusualwhales.com/docs/operations/PublicApi.TickerController.gex_levels)
- API 历史回看：Starter 套餐 1 年，Basic/Advanced 2 年，API Trial 3 个月 — [Unusual Whales API](https://unusualwhales.com/api_lander)（搜索摘要）
- Data Shop 出售日频 GEX 文件（put GEX、call GEX、net GEX、put/call GEX 比），格式 CSV/NDJSON/Parquet，标价 1 年数据 $10；另有 2019-2026 日频 gamma_exposure CSV 的条目 — [Unusual Whales GEX Data Shop](https://unusualwhales.com/data_shop/gamma_exposure)；[Data Shop](https://unusualwhales.com/data_shop)

**FinzData（付费）**
- 点时（point-in-time）历史 GEX：单一标的 5 年日频 $29，自 2010 年 1 月起全历史 $59；免费层仅最近 30 天 — [FinzData](https://finzdata.com/point-in-time-gex)；[FinzData 指南](https://finzdata.com/guides/best-historical-gex-data-api)
- 声称 SPX GEX 覆盖 2010-01 至 2026-10 — [FinzData SPX history](https://finzdata.com/guides/spx-gamma-exposure-history)

**FlashAlpha（付费，同时是多篇"回测"文章的作者，利益相关）**
- 声称分钟级报价与 Greeks 支持历史 GEX，结算 OI 与曲面参数为日度版本；覆盖"自 2017 年起分钟级" — [FlashAlpha Historical GEX API](https://flashalpha.com/articles/historical-gex-api-backtesting-gamma-exposure-strategies)
- 冲突：另有说法称其 SPX 历史 GEX 从 2022-01-05 开始 — 搜索摘要（未区分出自 [FinzData SPX 指南](https://finzdata.com/guides/spx-gamma-exposure-history) 还是 [FlashAlpha](https://flashalpha.com/articles/historical-gex-api-backtesting-gamma-exposure-strategies) 页面；两处起始日期不一致，需向供应商核实）
- 其建议：回测应使用每根 K 线时点的 GEX 值而非日终值，因为净 GEX 可在日内翻转，用收盘 GEX 标注 10:30 的入场等于使用了当时不存在的信息 — [FlashAlpha](https://flashalpha.com/articles/historical-gex-api-backtesting-gamma-exposure-strategies)

**其他/免费**
- dhawalc/spx-gamma-levels（GitHub，CC BY 4.0）：每日 SPX call wall、put wall、zero-gamma flip、vol trigger，CSV/JSON，每行带 `oi_settle_date`；但序列从 **2026-07-28** 才开始，对 2019-2026 回测无用 — [GitHub](https://github.com/dhawalc/spx-gamma-levels)
- OptionCharts 提供 $SPX GEX 历史，但完整历史需升级付费（页面较旧，价格可能已变）— [OptionCharts](https://optioncharts.io/options/$SPX/option-history)
- RetailGex：Pro 月付 $24.99、年付 $224.91，称含完整历史回看但深度未知 — [RetailGex](https://retailgex.csaini.org/)
- GEXStream：月付起价 $49.50，3 天试用 — [GEXStream](https://gexstream.com/)
- AlgoStorm：免费每日 SPX call wall / put wall / gamma flip（基于延迟 Cboe 数据），无可下载历史 — [AlgoStorm](https://algostorm.com/gex/)
- 原始期权数据：Historical Option Data 提供美股期权 2002 年至今、"ALL SPX since 1990" 的一次性购买（原始数据，需自行计算 GEX）— [Historical Option Data](https://historicaloptiondata.com/)
- Cboe 免费提供完整 SPX 期权链 JSON（全部行权价和到期日，含 OI 与隐波），延迟约 15 分钟（仅当前快照，非历史）— 搜索摘要（未能区分具体出处，候选为 [Squawkflow](https://squawkflow.com/gex) 或 [Perfiliev](https://perfiliev.com/blog/how-to-calculate-gamma-exposure-and-zero-gamma-level/)；使用前请到 Cboe 官网确认端点）

**Cboe 研究（交易所，可见真实交易方向，但有商业利益）**
- Cboe 的 "0DTEs Decoded" 系列描述 0DTE 仓位与市场影响 — [Cboe Insights](https://www.cboe.com/insights/posts/0-dt-es-decoded-positioning-trends-and-market-impact)
- Cboe 托管的 0DTE 波动影响论文（见第 1 节）— [Cboe PDF](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)

### Inferences
- 性价比排序（针对 2019-2026 日频体制过滤）：SqueezeMetrics GEX.csv（免费）> Unusual Whales Data Shop（约 $10/年，2019 起，且可选成交量口径）> FinzData（$59 全历史）。三者方法不同，可作为互相稳健性检验：若过滤效果只在一家数据上出现，很可能是噪声。
- 若要检验"开盘时相对 zero-gamma 位置"或日内 gamma 翻转，需要分钟级或至少开盘时点的数据（FlashAlpha 声称有，但起始年份说法冲突），或自行用历史期权链重建（见第 5 节）。
- 学术界普遍使用的 Cboe Open-Close（带买卖方向和客户类型）数据可以直接识别做市商/客户的净头寸，避免"dealer 多 call 空 put"的假设，但需付费购买（本次未查到价格）。

### Gaps
- MenthorQ、Tier1Alpha 的历史数据长度、格式和价格：本次搜索未得到任何可核实信息（MenthorQ 仅检索到 0DTE 科普页 [MenthorQ](https://menthorq.com/guide/all-about-0dte-options/)）。
- SpotGamma 是否向订阅用户提供历史 Volatility Trigger / Zero Gamma / Call Wall 序列：未找到证据。
- Cboe DataShop（Open-Close Volume、历史 OI）的具体价格与起始日期：未查到。
- Unusual Whales 日频 GEX 文件的具体方法（OI 口径还是方向化成交量口径）与是否点时（无回填）：未核实。

## 4. 实践规则、公开回测结果，以及 0DTE 如何改变 dealer gamma 效应

### Takeaway
实践者的通行规则是"价格在 zero-gamma / volatility trigger 之上 → 均值回归、区间震荡；之下 → 趋势、波动扩张"，但公开的严谨回测很少：唯一找到的"预注册"日频回测（2018-2026，1,972 个 SPY 交易日）显示 GEX 与次日已实现波动 Spearman ρ=-0.36，但控制 VIX 与 ATM 隐波后仅剩约 40% 的原始强度——GEX 更像"平静体制标签"，而不是独立 alpha；没有找到任何经过同行评审或可复制的"正 gamma 下 fade 获利"的回测。0DTE 现已占 SPX 成交约 59%，学术证据倾向于认为做市商 0DTE gamma 平均为正、抑制而非放大日内波动，但效应规模被 Cboe 认为"不大"。

### Cited Findings

**实践规则（多数为供应商/营销）**
- SpotGamma："价格在 Volatility Trigger 之上，dealer 正 gamma，倾向卖涨买跌、压制波动；之下进入负 gamma，倾向追涨杀跌、放大波动"（营销描述，且官方自己强调跌破只是"情境"）— [SpotGamma Volatility Trigger](https://spotgamma.com/volatility-trigger-zero-gamma-trading/)；[SpotGamma 负 gamma 解释](https://spotgamma.com/negative-gamma-explained/)；[SpotGamma 如何交易 GEX](https://spotgamma.com/how-to-trade-gex-levels/)
- 正/负 gamma 体制的交易手册类文章（均为营销/教育内容）— [Squawkflow](https://squawkflow.com/learn/positive-gamma-vs-negative-gamma)；[OptionScout](https://optionscout.ai/blog/negative-gamma-trading-playbook)
- Profitabul 表格称正 gamma 下均值回归胜率 70-82%，负 gamma 下 45-55%；**无方法和样本量说明，视为未经验证的营销数字** — [Profitabul](https://www.profitabul.com/learn/gex-regime-performance)

**公开回测（按可信度排序）**
- "I Backtested My Own GEX Product Across 8 Years of SPY. Most of It Is Just VIX."：预注册研究，2018-2026 年 1,972 个 SPY 交易日；GEX 与次日已实现波动 Spearman ρ=-0.36；控制 VIX 和 ATM IV 后 GEX 仍显著但仅约为原始强度的 40%；GEX/DEX/VEX/CHEX 在控制后增量很小；作者结论是 GEX 最适合作为"平静体制标签"，而非独立预测；**仅日终数据，未检验日内行为**；作者为 GEX 产品供应商（与 FlashAlpha 文章内容近乎相同）— [DEV Community](https://dev.to/tomasz_dobrowolski_35d32c/i-backtested-my-own-gex-product-across-8-years-of-spy-most-of-it-is-just-vix-a53)；[FlashAlpha 同文](https://flashalpha.com/articles/gex-dex-vex-chex-8-year-backtest-spy-vix-control)
- Build Alpha（2004-2026 第三方分析）：最低 GEX 五分位的次日波幅约为最高五分位的 3 倍；秩相关在近年减弱但仍为负（GEX 为 -0.20）— [Build Alpha](https://www.buildalpha.com/gamma-exposure-gex/)
- FlashAlpha 提出"正 gamma 体制下 15:30 至收盘收益应更小、更均值回归"的检验方法，但未报告结果 — [FlashAlpha](https://flashalpha.com/articles/historical-gex-api-backtesting-gamma-exposure-strategies)
- 论坛：GEX 与未来带符号收益无关，与未来波动 r²≈0.15 — [Elite Trader](https://www.elitetrader.com/et/threads/dealer-gamma-institutional-options-market-making.340500/page-5)
- 搜索未找到 Quantpedia 或 Robot Wealth 关于 GEX 体制过滤日内反转的回测（Quantpedia 仅有对 Adams 等 0DTE 论文的总结）— [Quantpedia](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)

**"正 gamma 失效"的案例与批评**
- 有 Substack 专文讨论正 gamma 体制下均值回归失效的情形，并指出 Anderegg 等 2022 年的样本中只有负 gamma 一侧有实证、正 gamma 一侧主要是理论推导（博客，谨慎对待）— [VolArchitect](https://dn12448583.substack.com/p/when-positive-gamma-fails)

**0DTE 的变化**
- 2025 全年 SPX 0DTE 日均成交创纪录约 230 万张，占 SPX 总成交 59%（另一处摘要给出约 260 万张，数字有出入）— [MarketsMedia: Cboe 2025 年报](https://www.marketsmedia.com/cboe-reports-record-trading-volume-for-2025/)
- 2025 年 2 月 0DTE 占比 56%、5 月超过 61%、8 月达 62.4%（日均约 240 万张）；8 月散户约占 0DTE 成交 53%，4 月初波动飙升期间降至 47% — [Cboe 2 月](https://www.cboe.com/insights/posts/spx-0-dte-options-jumped-to-record-56-share-in-feb/)；[Cboe 5 月](https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-61-share-on-retail-resurgence)；[Cboe 8 月](https://www.cboe.com/insights/posts/spx-0-dte-options-jump-to-record-62-share-in-august)
- 学术：做市商 0DTE 净 gamma 平均为正，负向预测日内波动，正 gamma 强化反转、负 gamma 强化动量 — [SSRN 4692190](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190)
- 学术：有 0DTE 的日子波动更低；净 gamma 变化对波动的抑制约 10 分钟内显现、约 1 小时后消退 — [Quantpedia](https://quantpedia.com/do-sp500-0dtes-options-increase-market-volatility/)；[Fontaine PDF](https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf)
- Cboe：做市商 0DTE 净 gamma 仅占 S&P 期货日流动性 0.04%-0.17%；gamma 引起的波动变化约 3.3 个百分点"并不大"，平均影响为降低约 0.2 个百分点 — [Cboe PDF](https://cdn.cboe.com/resources/education/research_publications/gammasqueezes.pdf)
- 0DTE 使用 OI 口径的 GEX 遗漏当日新开仓：OI 每日结算更新一次，日内水平基于前一日结算 OI — [GitHub dhawalc](https://github.com/dhawalc/spx-gamma-levels)（README 的 `oi_settle_date` 字段）；Unusual Whales 因此提供"成交量口径"的 GEX — [Unusual Whales API](https://api.unusualwhales.com/docs/operations/PublicApi.TickerController.gex_levels)

### Inferences
- 按现有证据，最稳健的经验事实是"GEX 低/负 → 次日波动大"，这与 VIX 高度重叠；"GEX 正 → fade 有正期望"没有被可信的公开回测证实。我们的过滤器检验应以"在控制 VIX 后 GEX 是否仍能区分 fade 盈亏"为核心假设，而不是"GEX 正时 fade 是否盈利"。
- 由于 0DTE 占比在 2022 年后急剧上升，且 0DTE 仓位不出现在前一日 OI 中，基于 OI 的日频 GEX 对 2022 年后开盘行为的解释力可能下降；应分 2019-2021 与 2022-2026 两段分别检验。
- Adams 等发现 gamma 对波动的抑制只持续约 1 小时，这提示开盘时点的 gamma 状态（而非前一日收盘）才是与开盘一小时 fade 匹配的变量——这需要日内数据。
- 0DTE 的短期 put 买盘集中在跳空低开日时，做市商可能是空 gamma（与"平均为正"不同），这正是我们策略的交易日类型，平均意义上的结论可能不适用于条件样本。

### Gaps
- 未找到任何同行评审或可复制的"zero-gamma 之上/之下"日内趋势日 vs 区间日的统计（如趋势日比例、开盘区间突破率）。
- 未找到 Robot Wealth、Quantpedia、Alpha Architect 对 GEX 体制过滤日内策略的独立回测（Alpha Architect 有一篇 "Hot Topic: Does 'Gamma' Hedging Actually Affect Stock Prices?" — [链接](https://alphaarchitect.com/hot-topic-does-gamma-hedging-actually-affect-stock-prices/)，但页面被网络拦截，未能读取内容）。
- 未能核实 SPX 增加周二/周四到期（形成每日到期）的具体日期（搜索未返回 Cboe 产品公告）。
- 2024-08-05 有二手来源称 SPX dealer gamma 为 2018 年 2 月以来最负，未能核实来源。

## 5. 没有供应商数据时如何用公开 OI 近似 GEX（方法与陷阱）

### Takeaway
标准做法是对整条 SPX（和/或 SPY）期权链按"call 记正、put 记负"累加 Gamma × OI × 合约乘数 × S² × 0.01（得到"每 1% 价格变动的美元 gamma"），再在一组假设现货价上重算全链 gamma 求 zero-gamma 点。主要陷阱是：符号假设（dealer 多 call 空 put）不可观测、OI 每日只更新一次（0DTE 盲区）、spot 是否平方的单位混乱、多个零点的选择、隐波/利率输入、以及远期/零 OI 合约的过滤。

### Cited Findings
- Perfiliev 公式：单合约 GEX = Gamma × 合约乘数 × OI × Spot，put 乘 -1；但其代码使用 `OI * 100 * S * S * 0.01 * gamma`（spot 平方并按 1% 变动缩放），文章中两种形式并存，容易弄错单位 — [Perfiliev](https://perfiliev.com/blog/how-to-calculate-gamma-exposure-and-zero-gamma-level/)
- 其他实现的单位也不一致：gex-tracker 仓库公式文字中 spot 乘一次，而笔记中写成 spot 平方 — [GitHub gex-tracker](https://github.com/Matteo-Ferrara/gex-tracker)；FlashAlpha 使用 spot 平方 × 100 × 0.01，call 正 put 负 — [FlashAlpha 计算示例](https://flashalpha.com/articles/how-to-calculate-gamma-exposure-gex-formula-worked-example)
- 所有实现都假设 dealer 多 call、空 put，这是建模假设而非观测事实，决定了总量符号 — [GitHub gex-tracker](https://github.com/Matteo-Ferrara/gex-tracker)；[Perfiliev](https://perfiliev.com/blog/how-to-calculate-gamma-exposure-and-zero-gamma-level/)
- Zero-gamma 不是当前 GEX 的符号翻转点：需在每个假设 spot 上重算每个合约的 gamma（不能简单缩放），再找总 gamma 穿越零的位置 — [Perfiliev](https://perfiliev.com/blog/how-to-calculate-gamma-exposure-and-zero-gamma-level/)；[SpotGamma](https://spotgamma.com/gamma-exposure-gex/)
- 可能出现多个零点；有数据集取"距现价最近的零点" — [GitHub dhawalc](https://github.com/dhawalc/spx-gamma-levels)
- 数据过滤：剔除 OI 为 0、无隐波、或行权价偏离现价超过 50% 的合约 — [David Arias Python 教程](https://davidariasfinance.com/scripts/gamma-exposure-gex/)
- OI 每日结算才更新一次，日内水平基于前一交易日结算 OI；dhawalc 数据每行记录 `oi_settle_date` 以保证可追溯 — [GitHub dhawalc](https://github.com/dhawalc/spx-gamma-levels)
- 利率设为零对数小时内 gamma 影响很小，但应明确说明 — 搜索摘要中某一 GEX 教程/数据集页面（未能区分具体出处，候选为 [GitHub dhawalc](https://github.com/dhawalc/spx-gamma-levels) 或 [Squawkflow](https://squawkflow.com/gex)）
- Cboe 免费提供完整 SPX 期权链 JSON（含 OI 与隐波），延迟约 15 分钟——可用于从今天起向前积累自有数据，但无历史 — 搜索摘要（未能区分具体出处，候选为 [Squawkflow](https://squawkflow.com/gex) 或 [Perfiliev](https://perfiliev.com/blog/how-to-calculate-gamma-exposure-and-zero-gamma-level/)；使用前请到 Cboe 官网确认端点）
- Zero Gamma 依赖库存假设、波动、时间和纳入的期权范围，不同供应商结果不同 — [SpotGamma](https://spotgamma.com/gamma-exposure-gex/)
- 自建历史需要购买原始期权链（如 Historical Option Data：SPX 自 1990 年）— [Historical Option Data](https://historicaloptiondata.com/)

### Inferences
- 对 2019-2026 回测，自建 GEX 的最低数据要求是：每日 SPX（+SPY）全链 EOD 的 OI、隐波（或可反推隐波的价格）、标的收盘价；计算 t-1 日结算 OI 下、t 日开盘价处的 GEX 和 zero-gamma 距离（开盘价已知，OI 已知，因此无前视）。
- 为减轻"dealer 多 call 空 put"假设的偏差，可做敏感性：(a) 标准假设；(b) 只计 put 侧；(c) 用 Cboe Open-Close 的客户方向数据（若能购买）重建真实做市商净头寸，比较三者对 fade 收益的区分能力。
- 0DTE 当日新开仓无法用 OI 捕捉；如需近似，可用当日开盘后成交量按"客户买 put / 卖 call"方向化（Unusual Whales 的"成交量口径"即此思路），但这需要带方向的分钟级成交数据。
- 单位统一：建议统一用"每 1% 变动的美元 gamma"（S²×0.01），并把 SPX（乘数 100）与 SPY（乘数 100，价格约为 SPX/10）合并时换算到同一名义单位。

### Gaps
- 未找到对"自建 OI-GEX 与 SqueezeMetrics/SpotGamma 序列相关性"的公开比较。
- 未找到 Cboe Open-Close 数据的价格、起始日期、以及学术论文使用其重建 SPX 做市商 gamma 的具体步骤（Baltussen 与 Dim-Eraker-Vilkov 很可能使用该类数据，但未核实）。
- 是否应纳入 SPY、ES 期货期权、QQQ 等关联产品的 gamma（跨产品对冲）——未找到定量研究。

## 6. 由目标推导：如何把"仅在正 gamma 体制下做 fade"变成可证伪的回测

### Takeaway
现有证据足以支持把 GEX 当作**候选体制变量**来测试，但不足以预期它会把一个 Sharpe≈0 的策略变成正 Sharpe；最低成本方案是用 SqueezeMetrics GEX.csv（t-1 日值）+ Unusual Whales/FinzData 做交叉验证，核心检验是"控制 VIX 后 GEX 分组的 fade 收益差异"，并分 0DTE 前后两段。

### Cited Findings
- GEX 与次日波动的关系在控制 VIX/ATM IV 后只剩约 40% — [DEV Community](https://dev.to/tomasz_dobrowolski_35d32c/i-backtested-my-own-gex-product-across-8-years-of-spy-most-of-it-is-just-vix-a53)
- 用日终 GEX 标注日内入场会引入前视偏差 — [FlashAlpha](https://flashalpha.com/articles/historical-gex-api-backtesting-gamma-exposure-strategies)；SqueezeMetrics 官方提醒 DATE 不保证收盘时可得 — [SqueezeMetrics guide.pdf](https://squeezemetrics.com/monitor/static/guide.pdf)
- 首半小时为正时日内动量更强（与 fade 早盘反弹方向相反）— [Gao et al. 工作论文](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- 指数日内动量在 NGE 为负时存在、越负越强 — [Baltussen et al.](https://academicweb.nd.edu/~zda/intramom.pdf)
- 正（负）做市商 gamma 强化日内反转（动量）— [Dim, Eraker & Vilkov](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190)

### Inferences
- 建议的检验步骤（均为推论，非文献结论）：
  1. 数据：SqueezeMetrics GEX.csv 的 GEX（及 GEX+）与 DIX，取 t-1 日值；同时下载 Unusual Whales 2019-2026 日频 net GEX 作为第二来源。
  2. 先做描述性检验，不做优化：把现有全部 fade 信号按 t-1 日 GEX 的符号、以及在 2019-2026 内的分位数（3 或 5 组）分组，比较每组的平均收益、胜率、t 值、Sharpe 和样本数。
  3. 关键控制：在回归 `fade_PnL ~ GEX_rank + VIX_rank + GEX_rank×VIX_rank` 或"VIX 分组内再按 GEX 分组"中检验 GEX 是否有增量；如果 GEX 效应在 VIX 控制后消失，就与已知的"VIX 区分不了"一致，可以放弃此方向。
  4. 分段：2019-2021 vs 2022-2026（0DTE 占比激增），以及剔除 2020-03 极端期，检验稳定性。
  5. 第二变量：开盘价相对 zero-gamma 的距离（需自建或分钟级供应商数据），因为 Adams 等发现 gamma 效应只持续约 1 小时，开盘时点状态比前一日收盘更贴近开盘一小时交易。
  6. 预期样本问题：跳空低开日的 GEX 往往偏低，正 gamma 子样本可能很小；需报告每组样本量，并用 bootstrap/置换检验评估显著性，并对测试的变量数量做多重检验校正（我们已测试过价格、成交量、VIX、趋势等多个过滤器）。
  7. 反向检验：如果理论正确，负 gamma 日 fade 应显著更差，而顺势（追随早盘方向）在负 gamma 日应更好；这一"对称预测"比单边过滤更能证伪假说。
- 合理的先验：文献支持"负 gamma 日不要 fade"的可能性大于"正 gamma 日 fade 能赚钱"；最现实的收益可能是剔除最差的一部分交易、降低尾部亏损，而不是把整体 Sharpe 提高到显著为正。

### Gaps
- 没有任何公开研究可以提供"GEX 过滤后开盘 fade 的预期 Sharpe"作为基准；以上流程的效果只能通过我们自己的回测确定。
- SqueezeMetrics 历史值是否存在方法改版回填，会影响 t-1 值是否真正"点时"，需实际下载后检查（本次网络受限未能完成）。

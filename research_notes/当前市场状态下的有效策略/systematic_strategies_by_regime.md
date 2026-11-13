# 系统化策略的 regime 条件表现（美股，温和回调 / 中等隐含波动 / 通胀再加速）

> 研究日期：2026-11-13（盘前）。研究对象状态：SPY 低于 50 日 SMA 约 0.9%、低于 20 日 SMA 约 0.3%，近 5 个交易日反弹 +3.3%；VIX ≈ 18.7（15–20 区间），VIX/VIX3M ≈ 0.93（contango）；14 日 ATR ≈ 价格的 1.64%（偏高）；US PPI +6.5% y/y，美联储官员偏鹰。
> 本文为研究笔记，不构成投资建议。
> 方法说明：本会话网络白名单限制，WebFetch 访问 trendfollowing.com、cdn.cboe.com、twosigma.com 全部失败（DNS 无法解析），因此几乎所有数字来自 WebSearch 返回的摘要/片段，未能逐页核对原文表格。凡是“摘要转述、未核对原文”的数字均已标注。证据等级标记：【同行评审】= 期刊论文；【工作论文】= SSRN/NBER/arXiv；【机构研究】= 资产管理人/指数商研究（存在商业动机）；【博客/营销】= 个人博客、vendor 或推广文案。

## 1. Trend following / time-series momentum：在股指回调与回撤中的表现（crisis alpha vs 震荡回调；2022 与 2018 Q4）

### Takeaway
长期证据【同行评审】显示 TSMOM 在“极端”行情（大牛市、大熊市）表现最好，呈“smile”形状，并在一个世纪里 10 次最大 60/40 回撤中的 8 次赚钱；但这种 crisis alpha 主要出现在持续数月的深度回撤中，在小幅、V 形、来回拉锯的回调里 trend 往往滞后甚至被 whipsaw。2022（通胀 + 鹰派联储）是 trend 的教科书式好年份（SG Trend Index 约 +27%），收益主要来自利率/外汇而非股指；2018 Q4 的短促急跌则表现参差，未找到精确季度数字。

### Cited Findings
- 【同行评审】Moskowitz, Ooi & Pedersen (2012)，"Time Series Momentum"，*Journal of Financial Economics* 104(2): 228–250；样本为 58 个流动性期货/远期合约（股指、货币、商品、债券）— [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:228-250)；[SSRN](https://papers.ssrn.com/abstract=2089463)
- 【同行评审】MOP 摘要：分散化 TSMOM 组合有显著 abnormal returns，对标准资产定价因子暴露很小，且“performs best during extreme markets”；Quantpedia 补充称收益在股市收益最极端时最大 — [RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:228-250)；[Quantpedia](https://quantpedia.com/strategies/time-series-momentum-effect/)
- AQR 公开的 MOP 原始数据：月度 TSMOM 因子，1985-01 至 2009-12，12 个月回看、1 个月持有 — [AQR dataset](https://www.aqr.com/insights/datasets/time-series-momentum-original-paper-data?aqrPDF=1)
- 分散化 TSMOM 组合 Sharpe：Quantpedia 报 1.31；另一博客称约 1.0（25 年）。两者冲突，需核对论文 Table 3 — [Quantpedia](https://quantpedia.com/strategies/time-series-momentum-effect/)；与 [Menon Lab 博客](https://themenonlab.blog/blog/time-series-momentum-hedge-fund-strategy-explained) 不一致
- 【同行评审，摘要转述未核对原文】Hurst, Ooi & Pedersen "A Century of Evidence on Trend-Following Investing"：TSMOM 在一个多世纪里 10 次最大 crisis（定义为 60/40 组合最大回撤）中的 8 次表现良好；1880–2016 年 10 次最大 60/40 回撤的平均峰谷时长约 15 个月；策略在大牛市与大熊市中表现最好（"smile" 图） — [Semantic Scholar](https://www.semanticscholar.org/paper/A-Century-of-Evidence-on-Trend-Following-Investing-Hurst-Ooi/3208cbb9fd9c146f8018a59c78fc69eac320c3b8)；[ResearchGate](https://www.researchgate.net/publication/318390566_A_Century_of_Evidence_on_Trend-Following_Investing)；[PDF 镜像](https://www.chesler.us/resources/academia/A_Century_of_Evidence_on_Trend_Following.pdf)
- 同文早期 2012 草稿检视 1903 年以来 10 次最大回撤，认为 2009–2012 的 trend 回撤放在长期背景下并不异常 — [Semantic Scholar](https://www.semanticscholar.org/paper/A-Century-of-Evidence-on-Trend-Following-Investing-Hurst-Ooi/3208cbb9fd9c146f8018a59c78fc69eac320c3b8)
- 【机构研究】Return Stacked：trend 在熊市“第一拳”（first leg）通常滞后，分散化收益历史上主要出现在从 -10% 一路磨到底部的阶段；并称大型熊市很少止于 -10% — [Return Stacked](https://www.returnstacked.com/trend-following-through-turmoil-why-the-best-protection-comes-after-the-first-punch/)
- 【机构研究】Man Group：V 形反弹在多种环境中都出现过（包括 2001–2003 长期下跌期间），并未发现向更快反弹的结构性转变 — [Man: Are V-Shaped Recoveries Becoming More Frequent?](https://www.man.com/insights/views-from-the-floor-2025-June-10)
- 【机构研究】Man Group 另文称，美国政策“时开时关”造成的 whipsaw 在 2025 年伤害了 trend-following（检索摘要将此归于 Man 文章，来源与链接的对应关系未逐字核对） — [Man: Trend Following and Drawdowns: Is This Time Different?](https://www.man.com/insights/is-this-time-different)
- 【博客，方法不透明】quantdecoded（10 个月均线规则）：trend 在持续 6 个月以上的熊市最有效，在 V 形崩盘中失效；1900–2025 年 trend 相对 buy-and-hold 年化落后约 0.7%，视为“保险费” — [quantdecoded](https://quantdecoded.com/en/trend-following-vs-buy-and-hold-bear-market-survival)
- 【博客】长仓 trend following 历史上主要作用是降低回撤与波动，而非显著提升收益 — [Systematic Individual Investor](https://systematicindividualinvestor.com/2017/07/22/is-trend-following-a-figment-of-the-imagination/)
- 【行业媒体】2022：SG Trend Index +27.3%，为 SG 各 CTA 指数之首；SG CTA Index 约 +20.1%/+20.2%；收益主要来自固定收益、外汇（全球国债价格下跌、美元走强） — [Hedgeweek](https://www.hedgeweek.com/trend-followers-turn-leaders-ctas-deliver-record-returns-2022/)；[Alpha Week](https://www.alpha-week.com/2022-cta-index-performance-review)
- 【行业媒体】2010 年代 SG Trend Index 年化仅约 1.8% — [Hedgeweek](https://hedgeweek.com/news/trend-followers-turn-leaders-ctas-deliver-record-returns-2022)
- 【机构研究】Man AHL：主动策略中 trend-following 在重要通胀冲击期间提供最可靠的保护；假设性全资产 trend 组合在美国通胀 regime 中实际 CAGR 约 25%；同期股票实际年化收益约 -7%（Neville, Draaisma, Funnell, Harvey, Van Hemert） — [Man: The Best Strategies for Inflationary Times](https://www.man.com/insights/best-strategies-for-inflationary-times)；[Duke 发表版 PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P154_The_best_strategies.pdf)
- 2018 Q4：PIMCO 评论称“并非所有 managed futures 策略都成功应对了近期的波动，例如 2018 年第四季度”，较短的股市抛售期间各基金结果分化 — [Advisor Perspectives / PIMCO](https://www.advisorperspectives.com/commentaries/2021/06/21/pimco-trends-managed-futures-seeking-diversification-and-returns)
- 2018 年 12 月：Top Traders Unplugged 早期估计“所有主要 CTA 指数 12 月均上涨”，即投资者期待的与股票负相关；并称 1999 年以来 SG Trend Index 表现最好的三个月是 11 月、12 月、1 月 — [Top Traders Unplugged](https://www.toptradersunplugged.com/market-trends-december-2018/)
- 【工作论文】arXiv 有新论文从微观结构角度讨论“短期 trend-following 的消亡”（仅见标题，未读内容） — [arXiv 2607.01550](https://arxiv.org/pdf/2607.01550)

### Inferences
- 当前回调幅度极小（SPY 仅低于 50 日 SMA 约 0.9%），且已出现 +3.3% 的 5 日反弹，这属于 trend 最不擅长的“浅回调 + 快速反弹”形态：股指 trend 信号（20/50 日级别）处于翻转边缘，whipsaw 风险高；crisis alpha 的历史证据集中在持续约 15 个月、深度远超 10% 的回撤，不适用于当前这种 1–5% 级别的回调。
- 但多资产 trend 的收益来源不止股指。若通胀再加速（PPI +6.5% y/y）+ 鹰派联储延续，2022 年式的利率/外汇/商品趋势可能再次成为 trend 的主要驱动；这是 trend 在当前宏观 regime 中最有依据的正面论点（Man 通胀研究 + 2022 实证），而非股指 crisis alpha。
- 2018 Q4（急跌 + 12 月 V 形底）与当前更像的情形是“短促股指回调”，证据显示 CTA 表现分化，不能指望稳定对冲。

### Gaps
- 未取得 SG Trend Index 2018 年 10–12 月逐月精确收益（SG 官网与 BarclayHedge 无法访问）。
- 未能核对 Hurst-Ooi-Pedersen 原文的回撤表（每次回撤的 trend 收益数字）与按通胀/利率环境拆分的表格；trendfollowing.com PDF 被网络白名单阻挡，需放行该域名后再取。
- 未找到按“回撤深度分组（如 5%、10%、20%）”系统统计 trend 收益的同行评审研究。

## 2. 股指短期均值回归 / buy-the-dip（RSI(2)、跌后买入、短期反转）：200/50 日均线上方还是下方、哪种 VIX 水平效果更好

### Takeaway
同行评审证据（Nagel 2012, RFS）表明短期反转（流动性提供）的期望收益和条件 Sharpe 随 VIX 上升而大幅提高，但该研究是横截面股票/行业反转，而非指数择时；指数层面的 RSI(2)/Connors 类规则几乎只有博客/书籍级证据，普遍使用“价格在 200 日均线上方”过滤，熊市（200 日下方）中胜率明显下降、尾部风险更大，且有一项带样本外检验的研究认为交易成本已吃掉大部分 edge。

### Cited Findings
- 【同行评审】Nagel (2012) "Evaporating Liquidity"，*Review of Financial Studies* 25(7): 2005–2039：以短期反转策略收益作为流动性提供收益的代理；其期望收益强烈时变、且可被 VIX 高度预测；在 2007–09 金融危机等动荡期，期望收益与条件 Sharpe 随 VIX 急升；用行业组合构造的反转策略无条件下几乎不赚钱，但在 VIX 高时收益和 Sharpe 很高；作者将其解读为受融资约束中介撤出流动性供给 — [NBER w17653](https://nber.org/papers/w17653)；[RePEc RFS](https://econpapers.repec.org/RePEc:oup:rfinst:v:25:y:2012:i:7:p:2005-2039)；[NBER PDF](https://www.nber.org/papers/w17653.pdf)
- 【汇总】Quantpedia：股票短期反转收益主要在大幅下跌之后的几周内上升，策略行为类似 short-volatility；在高波动的危机日交易反转可能很危险，因为会迫使买入跌得最多的股票 — [Quantpedia: Short Term Reversal](https://quantpedia.com/strategies/short-term-reversal-in-stocks)
- 【工作论文/会议论文】Della Corte & Kosowski "Market Closure and Short-Term Reversal"：高波动时中介活动受限，并将 VIX 变动与隔夜-日内反转相联系（摘录残缺，未能确认按波动 regime 的收益数字） — [CICF paper](https://www.cicfconf.org/sites/default/files/paper_357.pdf)
- 【同行评审，背景】Management Science 60(3) 2014 关于反转的论文（检索结果中出现，未读内容） — [Da 等, Reversal.pdf](https://academicweb.nd.edu/~zda/Reversal.pdf)
- 【独立研究站，样本外】Quanterlab 测试 S&P 500 上的 RSI(2)：一个变体为 RSI(2)<10、收盘价在 200 日均线上方、前一交易日 VIX ≥ 20 时买入，收于 5 日均线上方时卖出；采用冻结规则的样本外检验；标题结论为“RSI(2) 均值回归在 S&P 500 上的领先优势被成本吃掉”（只看到摘要，未见收益/回撤表） — [Quanterlab](https://quanterlab.com/research/navigating-mean-reversion-breaking-down-the-base-mechanism)
- 【博客】SPY 2000–2026，经典 RSI(2) + 200 日均线过滤：181 笔交易，胜率约 82%，Sharpe 0.62（buy-and-hold 0.53），仅约 10% 时间持仓 — [Guru Finance Insights](https://gurufinanceinsights.substack.com/p/i-backtested-the-classic-rsi2-mean)
- 【博客，数字间互相冲突、成本处理不明】另有 SPY 2000–2024 回测：387 笔交易、胜率 73%、profit factor 1.65，且熊市中少数触发交易的胜率降至 58%；还有一份报 406 笔、胜率 73.4%、profit factor 2.45、平均每笔约 1.4%，未计交易成本（检索摘要未明确对应具体是哪一篇） — [Backtest Everything](https://www.backtesteverything.com/blog/rsi-mean-reversion-strategy-complete-backtest)；[Loomi AI](https://www.loomiai.io/learn/rsi-2-mean-reversion-strategy/)；[QuantifiedStrategies](https://www.quantifiedstrategies.com/mean-reversion-trading-strategy/)
- 【书籍规则，结果为营销文案】Connors & Alvarez《Short Term Trading Strategies That Work》"VIX Stretches"：价格高于 200 日均线、VIX 连续 ≥3 天高于其 10 日均线 ≥5%、收盘买入，RSI(2) 上穿 65 退出；相关网站称“75% correct”，属推广文案，未见独立核验 — [EasyLanguage Mastery: VIX Stretch](https://easylanguagemastery.com/strategies/vix-stretch/)；[书籍摘要](https://tradelosstracker.com/library/book/16-short-term-trading-strategies-that-work-alvarez)
- 【博客】Thomas Carr VIX Reversal 一类规则据称在 VIX >20 或 >30 时更有效，但有回测评论认为“没有真实 edge”；证据为轶事级或短样本 — [WH SelfInvest](https://www.whselfinvest.com/en-lu/trading-platform/free-trading-strategies/tradingsystem/40-vix-reversal)；[TradingCode](https://www.tradingcode.net/tradingview/vix-reversal-system/)
- 【博客/通讯，样本与定义各异】200 日均线 regime 下的指数统计：一项 50 余年分析称 200 日下方年化收益 +4.1% vs 上方 +9.7%，波动率 25.0% vs 13.1% — [Stockopedia](https://www.stockopedia.com/content/the-sp-500-just-broke-below-its-moving-averages-heres-why-that-matters-1047835/)；另一份称 SPY 在 200 日上方年化波动 13.81% vs 下方 29.93% — [Free Market Speculator](https://freemarketspeculator.substack.com/p/the-200-day-line-in-the-sand)
- 【博客】1950 年以来“创一个月新低”的事件研究：收于 200 日下方时，下一季度中位收益 2.18%、胜率 59.77%；收于 200 日上方时中位 3.33%、胜率 73.57%（检索摘要未明确对应具体是哪一篇） — [Trader Markus](https://tradermarkus.com/sp-500-200-day-moving-average/)；[Potomac](https://potomac.com/blog/buy-the-dip)
- 【博客】长期测试认为 200 日均线对收益预测力很弱，主要价值在降风险：33 年里年化少赚 2.7 个百分点，换来更小回撤 — [Torvaq](https://torvaq.substack.com/p/deep-dive-7-replicating-the-200-day)

### Inferences
- 两类证据方向一致但层面不同：(a) 横截面/流动性提供层面，VIX 越高、反转收益越高（Nagel）；(b) 指数择时层面，实务规则普遍要求“200 日上方”才买 dip，因为 200 日下方的 dip 胜率和中位收益都更低、而波动约翻倍。所以“均值回归在高 VIX 时更赚钱”与“均值回归在熊市更危险”并不矛盾：期望收益更高但尾部更厚。
- 当前 VIX 18.7 属中等，Nagel 式的“高 VIX 溢价”只是部分存在；Quanterlab 变体要求前一日 VIX ≥ 20，当前不满足。
- 关键未知量：SPY 相对 200 日均线的位置（任务给出的只有 20/50 日）。若仍在 200 日上方，当前更接近“牛市中的回调”，历史上是 RSI(2)/buy-the-dip 最有利的情形；若已跌破 200 日，证据指向胜率下降（如 58% vs 70%+）。
- 5 日 +3.3% 反弹意味着 RSI(2) 类短线超卖信号大概率已经触发并兑现，当前时点更接近这类策略的“退出区”而非“入场区”（推断，需用实际数据验证）。

### Gaps
- 未找到以指数为对象、按 VIX 分桶（如 <15、15–20、20–30、>30）并给出样本期的同行评审 RSI(2)/跌后买入研究。
- Quanterlab 的完整收益/成本表、Connors 书中 VIX Stretch 的原始统计未能取得。
- 未找到“50 日均线下方但 200 日上方”这一中间状态的专门统计（与当前状态最相关）。

## 3. 防御型股票因子（low volatility、quality、value vs growth）在加息/通胀与回调 regime 中的表现

### Takeaway
在通胀上行、利率上行的 regime 中，low volatility 因子（带有类债券的利率久期暴露）普遍落后，2022–2023 尤其差；value 与 momentum 相对占优；quality 介于两者之间（Man 测算通胀期实际年化约 3%）。在纯粹的“回调/风险厌恶”中 low vol 通常能提供下行保护，因此当前“回调 + 通胀再加速”组合下，单独押注 low vol 的证据弱于 value/quality 混合或带 value 倾斜的低波。

### Cited Findings
- 【机构研究，发表于学术期刊】Man Group（Neville, Harvey 等）：股票因子提供部分通胀保护；momentum 在通胀 regime 中实际年化约 8%，正常时期约 4%；quality 通胀期平均约 3%；value 结果不一（不同摘要分别称“小幅负收益”与“有一定益处”，存在冲突）；trend 收益更高但容量有限，主要股票因子容量充足 — [Man: Best Strategies for Inflationary Times](https://www.man.com/insights/best-strategies-for-inflationary-times)；[Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P154_The_best_strategies.pdf)；[PA-PERS PDF](https://www.pa-pers.org/assets/docs/Falll%202021%20-%20Man%20Group%20full%20research%20paper.pdf)；另见 [Man: What Works When Inflation Hits?](https://www.man.com/insights/when-inflation-hits)
- 【机构产品】Man AHL 基于上述研究推出 TIDE，组合 trend 与 defensive equity quality 两部分 — [Man AHL TIDE](https://www.man.com/ahl-trend-inflation-defensive-equity)
- 【指数商研究】FTSE Russell（2003 年以来）：通胀预期上升时 Size 与 Value 表现更好；通胀预期下降时 Low Volatility、Quality、Momentum 更好；其表格中 2022–23 期间的模式与此大致相反（检索摘要表述含糊，未核对原表） — [LSEG / FTSE Russell](https://www.lseg.com/en/ftse-russell/research/factor-performance-under-different-inflation-regimes)；另见 [FTSE Russell: value in higher inflation, quality in a recession](https://www.lseg.com/en/insights/ftse-russell/how-to-find-value-in-higher-inflation,-and-quality-in-a-recession)
- 【机构研究，注意是信用市场】Robeco：利率上行时 low-risk/quality 因子跑输、value 表现强劲——此结论针对 corporate credit factor premiums，而非股票 — [Robeco](https://www.robeco.com/en-uk/insights/2022/10/are-credit-factor-premiums-robust-to-rising-inflation-and-interest-rates)
- 【实务研究】Alpha Architect：low-vol 收益与 term premium 暴露相关，利率下行是顺风、利率上行是逆风 — [Alpha Architect](https://alphaarchitect.com/low-volatility-strategies/)
- 【机构研究】BMO GAM：2022 和 2023 的特定环境对低 beta 策略“异常不利”；历史数据显示低波策略在加息周期落后基准、在其他时期跑赢 — [BMO GAM](https://institutional.bmogam.com/ca-en/insights/is-low-volatility-ripe-for-recovery/)
- 【机构研究，内部表述冲突】TD Asset Management：一处称低波策略在回撤中“表现出韧性”并在下跌市场提供下行保护，另一处称同年受冲击最大的是低波风格 — [TD AM 年度回顾](https://www.td.com/content/dam/tdcom/canada/tdam/en/investor/pdf/news-insight/low-volatility-investing-year-in-review-and-look-ahead-en.pdf)；[TD Retail Low Vol](https://td.com/ca/en/asset-management/documents/investor/PDF/news-insight/Retail-Low-Volatility-EN.pdf)
- 【实务媒体】当低波股票带 value 暴露时，平均跑赢市场 2.0 个百分点；带 growth 暴露时平均跑输 1.4 个百分点 — [Advisor Perspectives](https://www.advisorperspectives.com/articles/2022/10/31/the-underlying-risk-in-low-volatility-portfolios)
- 【CFA Institute 博客】2022 年因子表现很大程度由行业构成驱动：能源上涨推动 Value、Momentum、Low Investment，并拖累 Low Volatility 与 High Profitability — [CFA Institute Enterprising Investor](https://blogs.cfainstitute.org/investor/2023/03/31/will-factor-performances-comeback-persist)

### Inferences
- 当前“PPI 再加速 + 鹰派”的组合，按 FTSE Russell / BMO / Alpha Architect 的证据，对 low vol 是逆风（利率久期暴露）；按 Man 研究，momentum 与 quality 在通胀期仍有正的实际收益，value 结论不稳定。
- 但“通胀 regime”与“股指回调 regime”对 low vol 的作用方向相反：回调时 low vol 的低 beta 帮忙，通胀/利率上行时其类债属性拖累。2022 就是两者叠加、最终 low vol 表现不佳的案例（且受能源行业权重影响）。
- 实务含义（推断）：若要防御，带 value/quality 倾斜的低波（而非纯低波、或偏 growth 的低波）在证据上更站得住。

### Gaps
- 未找到 AQR "Quality Minus Junk" / "Betting Against Beta" 在加息或回调期间的分 regime 数字（未检索到可引用摘要）。
- 未找到针对“温和回调（5–10%）”这一特定深度的因子表现统计；现有证据多为“通胀 regime”或“全年 2022”。
- FTSE Russell 表格中 2022–23 的具体数值未能核对。

## 4. 波动率风险溢价（put writing / PUT 指数、short VIX futures、iron condor）：按 VIX 水平与趋势 regime 的表现

### Takeaway
长期看隐含波动系统性高于已实现波动（1990–2018 年 VIX 均值 19.3% vs 已实现 15.1%），PUT 指数以更低 beta、更浅回撤获得接近股票的收益，且 PUT 收益随 VIX 水平上升而提高；但 VRP 在动荡熊市、已实现波动跳升时会被吞噬，short VIX futures 在 bull market 最好、在 turbulent bear market 最差（2018 年 2 月为典型）。当前 VIX 18.7 接近长期均值、期限结构 contango，carry 为正；但 ATR 偏高意味着已实现波动可能接近甚至高于隐含波动，“卖波动”的安全垫偏薄。

### Cited Findings
- 【Cboe 委托学术研究】Bondarenko (2019)：平均已实现最大回撤 PUT -32.7%、WPUT（周度）-24.2%、S&P 500 -50.9%；PUT 收益总体随 VIX 水平上升而增加（检索摘要转述，cdn.cboe.com 无法访问原文表格） — [Bondarenko 2019, Cboe](https://cdn.cboe.com/resources/education/research_publications/PutWriteCBOE19_v14_by_Prof_Oleg_Bondarenko_as_of_June_14.pdf)；[Bondarenko 演示稿](https://assets.website-files.com/5ab57d66e05e2f5708989178/5ca2381206205817b201bab9_Day%203%20Session%202%20Oleg%20Bondarenko%20PUT%20PUTW%20(as%20of%20March%2021%20widescreen).pdf)
- 【Cboe】基于 Bondarenko 研究的白皮书：1990–2018 年平均隐含波动（VIX）19.3%，S&P 500 平均已实现波动 15.1%，溢价约 4.2 个波动点 — [Cboe Insights](https://www.cboe.com/insights/posts/white-paper-shows-volatility-risk-premium-facilitated-higher-risk-adjusted-returns-for-put-index/)
- 【顾问研究】Ennis Knupp：VIX 与 PUT 指数相关系数 -0.54，PUT 本质是 short volatility；当 VIX 回落至平均水平时，权利金收入也随之下降 — [Ennis Knupp, Cboe](https://cdn.cboe.com/resources/education/research_publications/PUTIndexEnnisKnupp.pdf)
- 【机构研究】Neuberger Berman：1986-06 至 2022-12，PUT 最大回撤 -38.4% vs S&P 500 -57.4%，对 S&P 500 beta 0.58 — [NB: Simply Put(Writing)](https://www.nb.com/-/media/NB/Article-Assets/u0346_1119_simply_putwriting.ashx)；[Cboe 镜像](https://cdn.cboe.com/resources/indices/whitepapers/Neuberger_Berman_Simply_PutWriting.pdf)
- 【机构研究】GMO（2018，2 月 5 日 VIX 事件后）：put writing 应预期比标的指数回撤更浅（未按 VIX 分桶） — [GMO](https://www.gmo.com/globalassets/articles/insights/global-equity/2018/ncvl_value-of-short-volatility-strategies_2-18.pdf)
- 【指数商/CFA Research Foundation】S&P DJI / Moran：做空 VIX futures 在牛市表现最好，在动荡熊市受损最大；VIX 期货曲线通常处于 contango — [CFA RF brief (Moran)](https://rpc.cfainstitute.org/sites/default/files/-/media/documents/article/rf-brief/rfbr-moran-vix-volatility.pdf)；[S&P DJI](https://www.spglobal.com/spdji/en/documents/research/research-the-vix-index-and-volatility-based-global-indexes-and-trading-instruments.pdf)
- 【vendor，方法未披露，视为未核实】paperswithbacktest：曲线倒挂当日的成本很高，2018 年空头一侧一年亏损约 92%；并估计做空长期约 +53%/年（扣除 VIX 自身变动后） — [Papers With Backtest](https://paperswithbacktest.com/strategies/vix-term-structure)
- 【vendor 启发式，非检验结果】低 VIX（<15）+ 陡峭 contango 有利于卖权利金；压力期曲线倒挂 — [Sharpnel Trading](https://www.sharpnel-trading.com/learn/vix-term-structure/)；[MenthorQ](https://menthorq.com/guide/vix-futures-term-structure/)
- 【工作论文】arXiv 变量动力学研究：short vol 是对隐含-已实现差的押注，但该溢价自身波动很大且难以预测 — [arXiv 1507.00846](https://arxiv.org/pdf/1507.00846)
- 【工作论文，2026】arXiv learning-to-rank VRP 论文：主张按 regime 条件收割而非静态卖出；其 Cboe PUT 结果在样本外减弱 — [arXiv 2608.24786](https://arxiv.org/pdf/2608.24786)
- 【学术工作论文】Monash 关于 S&P 500 卖 put 的实证：卖 put 并不保证比持有股票有更高的复合收益（检索摘要转述，样本细节未核对） — [Monash WP 2019-3](https://www.monash.edu/__data/assets/pdf_file/0010/1726228/WP_CQFIS_2019_3.pdf)
- 【机构研究】AQR "Understanding the Volatility Risk Premium"（2018 年 5 月；未取得具体分 regime 数字） — [AQR](https://www.aqr.com/-/media/AQR/Documents/White-Papers/Understanding-the-Volatility-Risk-Premium.pdf)
- 【汇总】Quantpedia VRP 条目 — [Quantpedia: VRP Effect](https://quantpedia.com/strategies/volatility-risk-premium-effect)
- 200 日均线下方指数年化波动约为上方的 2 倍（25.0% vs 13.1%；或 29.93% vs 13.81%），提示趋势转弱时已实现波动上升 — [Stockopedia](https://www.stockopedia.com/content/the-sp-500-just-broke-below-its-moving-averages-heres-why-that-matters-1047835/)；[Free Market Speculator](https://freemarketspeculator.substack.com/p/the-200-day-line-in-the-sand)

### Inferences
- VIX 18.7 与 1990–2018 长期均值 19.3 几乎相同，属于“正常”而非“高溢价”区间；按 Bondarenko “PUT 收益随 VIX 上升” 与 Ennis Knupp “VIX 回落时权利金下降”的证据，当前权利金厚度中性，不是卖波动的特别有利点。
- VIX/VIX3M ≈ 0.93 的 contango 意味着 short VIX futures 的 roll carry 为正，但 0.93 并不陡峭（vendor 启发式认为最有利的是 VIX<15 + 陡峭 contango）。
- 粗略换算（推断，需验证）：14 日 ATR 1.64% × √252 ≈ 26% 年化。ATR 包含跳空与日内振幅，通常高估收盘-收盘波动，但仍提示近期已实现波动可能接近或高于 18.7 的隐含波动，即短期 VRP 可能很薄甚至为负。这与“趋势转弱时已实现波动翻倍”的统计一致，是当前卖波动最主要的风险点。
- 结合 S&P DJI “short VIX 在 turbulent bear 中最差” 的结论：只要回调未演变为持续下跌，卖 put/iron condor 历史上多数时候获得补偿；若回调深化并伴随期限结构倒挂（VIX/VIX3M >1），损失呈非线性。可将 VIX/VIX3M 翻转至 >1 视为 regime 切换信号（这是从文献推出的风控思路，不是已检验结果）。
- 背景（仅见标题，未读内容）：2026 年 11 月有媒体标题称 “VIX Crashes 21%”（[Benzinga](https://www.benzinga.com/etfs/broad-u-s-equity-etfs/26/11/63062490/vix-crashes-21-as-wall-street-short-squeeze-accelerates-are-volatility-etf-bulls-losing-their-edge)），Saxo 11/12–11/13 市场速览标题提到 Nvidia 下跌拖累情绪、财报在下周二（[Saxo 11/12](https://home.saxo/en-sg/content/articles/macro/market-quick-take---nvidia-stumble-weighs-on-sentiment---12-november-2026-12112026)；[Saxo 11/13](https://home.saxo/en-mena/content/articles/macro/market-quick-take---nvidia-earnings-up-next-tuesday---13-november-2026-13112026)）。若属实，近期 VIX 已大幅回落，且临近单一大盘股事件风险，对卖短期限权利金不利。

### Gaps
- 未找到同时按 VIX 水平（15–20）与趋势状态（200/50 日下方）条件化的 PUT/BXM 或 short VIX 收益研究；Bondarenko 的 VIX 分桶具体数值因 cdn.cboe.com 被阻挡而未取得。
- 未找到 PUT/BXM 在 2018 Q4、2020-03、2022 各自的分段收益（需 Cboe 数据自行计算）。
- 未找到 iron condor 的系统性、同行评审级分 regime 研究；现有均为 vendor 资料。

## 5. Regime 分类框架（trend × volatility 象限、growth/inflation 象限、Two Sigma / Man AHL 等）及其报告的分 regime 策略表现

### Takeaway
可引用的框架主要有三类：(1) Two Sigma（2021）用 Gaussian Mixture Model 在其 Factor Lens 上识别出 Crisis、Steady State、Inflation、Walking on Ice 四种状态；(2) Man Group 以美国通胀 regime 划分，报告 trend 与股票因子的通胀期实际收益；(3) 学术/实务的“trend × vol”划分（极端行情 smile、200 日上下、VIX 分档）。当前状态在这些框架里最接近“Walking on Ice / 通胀”交界，而非 Crisis。但各框架的 regime 定义差异很大，数字不能直接互相换算。

### Cited Findings
- 【机构研究】Two Sigma，Botte & Bao（2021-10）"A Machine Learning Approach to Regime Modeling"：对 Two Sigma Factor Lens 的因子收益使用无监督 Gaussian Mixture Model，识别出 Crisis、Steady State、Inflation、Walking on Ice（WOI）四种市场状态；选择 GMM 是因资产收益分布有偏、尾部观测多 — [Two Sigma 文章](https://www.twosigma.com/articles/a-machine-learning-approach-to-regime-modeling/)；[Two Sigma PDF](https://www.twosigma.com/wp-content/uploads/2021/10/Machine-Learning-Approach-to-Regime-Modeling_.pdf)
- 二手来源：WOI 往往出现在 Crisis（及 Steady State）前后，可能代表市场脆弱；有片段显示 Market Condition 4 下 Momentum 为 19%（上下文缺失，无法确认比较口径）；另有自动生成文档称 WOI 中 Value、Momentum、Low Risk 波动显著高于长期均值（可靠性低） — [Regime-Based Alternative Allocation](https://investwithcarl.com/learning-center/investment-basics/dynamic-regimes-enhancing-alternative-investments-through-adaptive-allocation)；[Studocu 副本](https://www.studocu.com/in/document/indian-institute-of-technology-bombay/statistical-signal-analysis/machine-learning-for-regime-modeling-insights-applications/159988392)；[Scribd](https://www.scribd.com/document/691358379/Machine-Learning-Approach-to-Regime-Modeling)
- 【机构研究】SSGA（2025）"Decoding Market Regimes with Machine Learning"（Daniel Ung；仅见标题，未读内容） — [SSGA PDF](https://www.ssga.com/library-content/assets/pdf/global/pc/2025/decoding-market-regimes-with-machine-learning.pdf)
- 【机构研究，期刊发表】Man Group 通胀 regime 框架：股票通胀期实际年化约 -7%；全资产 trend 实际 CAGR 约 25%；momentum 8%（正常期 4%）、quality 约 3%、value 结论不一 — [Man](https://www.man.com/insights/best-strategies-for-inflationary-times)；[Duke PDF](https://people.duke.edu/~charvey/Research/Published_Papers/P154_The_best_strategies.pdf)
- 【同行评审】Trend × 市场极端度：TSMOM 在极端股市（大涨/大跌）表现最好（smile） — [MOP 2012, RePEc](https://econpapers.repec.org/RePEc:eee:jfinec:v:104:y:2012:i:2:p:228-250)；[Hurst-Ooi-Pedersen](https://www.semanticscholar.org/paper/A-Century-of-Evidence-on-Trend-Following-Investing-Hurst-Ooi/3208cbb9fd9c146f8018a59c78fc69eac320c3b8)
- 【同行评审】流动性/波动 regime：反转（流动性提供）收益随 VIX 上升 — [Nagel 2012, NBER](https://nber.org/papers/w17653)
- 【博客】趋势 × 波动简单象限（200 日上/下）：上方年化收益 +9.7%、波动 13.1%；下方 +4.1%、波动 25.0% — [Stockopedia](https://www.stockopedia.com/content/the-sp-500-just-broke-below-its-moving-averages-heres-why-that-matters-1047835/)
- 【指数商】short VIX futures：bull market 最好、turbulent bear 最差 — [S&P DJI](https://www.spglobal.com/spdji/en/documents/research/research-the-vix-index-and-volatility-based-global-indexes-and-trading-instruments.pdf)
- 【机构研究】trend 的“两阶段熊市”：第一段滞后，-10% 之后的磨底阶段才体现分散化价值 — [Return Stacked](https://www.returnstacked.com/trend-following-through-turmoil-why-the-best-protection-comes-after-the-first-punch/)

### Inferences

**当前状态映射（推断，综合上述证据；不是已检验结果）**

| 策略族 | 当前状态下的证据倾向 | 主要依据 | 主要风险/前提 |
|---|---|---|---|
| 多资产 trend / TSMOM | 中性偏正（来自利率/外汇/商品，而非股指） | Man 通胀研究；2022 SG Trend +27.3% | 股指层面处于 whipsaw 区；2025 年政策 whipsaw 曾伤害 trend |
| 股指 trend（20/50 日） | 偏负 | 浅回调 + V 形反弹是 trend 的弱项（Return Stacked、Man） | 若回调演变为 >10% 持续下跌则转正 |
| 指数短期均值回归（RSI(2) 等） | 若在 200 日上方偏正；跌破则下降 | 博客回测（胜率 70–80% vs 熊市 58%）；Nagel（VIX 越高越好） | 证据多为博客；成本可能吃掉 edge（Quanterlab）；5 日 +3.3% 后入场信号或已过 |
| Low volatility | 偏负（通胀/加息逆风） | FTSE Russell、BMO、Alpha Architect、CFA 2022 归因 | 若回调加深、风险厌恶主导，可能转为相对受益 |
| Quality | 中性偏正 | Man：通胀期实际约 3% | 证据较薄 |
| Value | 中性偏正（但证据冲突） | FTSE Russell：通胀预期上升期占优；Man：结论不一 | 2022 优势很大程度来自能源权重 |
| Momentum（股票横截面） | 中性偏正 | Man：通胀期实际 8% vs 正常 4% | 回调后的急速反转可能造成 momentum crash（本次未检索该方向证据） |
| 卖波动（PUT、short VIX、condor） | 中性偏谨慎 | VIX≈长期均值；contango 但不陡；ATR 提示已实现波动偏高 | VIX/VIX3M 翻转 >1、回调深化时损失非线性 |

- 在 Two Sigma 框架中，当前更像 “Walking on Ice”（介于 Steady State 与 Crisis 之间的脆弱状态）或 “Inflation”，而非 Crisis；但 Two Sigma 的 regime 是基于多因子收益分布估计的，不能用 VIX 或均线直接对应，此处只是定性类比。
- 不同框架的 regime 定义差异巨大：MOP/HOP 用“股市收益极端度”或“60/40 回撤”；Man 用“美国通胀 regime”；博客用“200 日均线上下”；Nagel 用 VIX 水平。将它们拼在一起得出的是方向性判断，而非可叠加的数字。
- 小样本警示：通胀 regime 在美国历史上次数很少（Man 研究以少数几次通胀期为样本），2022 是单一年份；2018 Q4、2020-03 等单次事件不足以支撑稳健结论。

### Gaps
- 未检索 Bridgewater All Weather 式 growth × inflation 四象限的公开分象限收益数据（本次检索预算内未覆盖）。
- Two Sigma 四种 regime 下各因子（Equity、Trend、Value、Low Risk、Momentum 等）的具体收益/波动表格未能取得（twosigma.com 被网络白名单阻挡）；如需数字，需放行 www.twosigma.com 后读取 PDF。
- 未找到 Man AHL 的“trend × vol 象限”类公开研究给出的分象限 Sharpe；也未取得 SSGA 2025 regime 论文的具体结论。
- 网络限制：www.trendfollowing.com、cdn.cboe.com、www.twosigma.com 需要在会话网络设置中放行，才能核对 Hurst-Ooi-Pedersen、Bondarenko、Ennis Knupp、Two Sigma 的原文表格。

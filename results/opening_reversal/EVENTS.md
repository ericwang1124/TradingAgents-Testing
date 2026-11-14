# Opening reversal short — scheduled-event days

- **Period**: 2019-01-02 to 2026-11-12 (1978 sessions); early/late split at 2023-01-01
- **Cells**: average R (number of trades)
- **macro_830**: pre-market volume burst at 08:30 >= 4.0x the 08:00-08:29 rate (catches ~88% of 2025-26 CPI/jobs days; about half the flags are other market-moving 8:30 data)
- **any_major_event**: FOMC day, day after FOMC, or macro_830
- **Generated**: 2026-11-13 05:07

## How common each event is

|                  |   % of sessions |
|:-----------------|----------------:|
| fomc_day         |             3.2 |
| fomc_next_day    |             3.2 |
| macro_830        |            16.9 |
| opex             |             4.8 |
| quad_witching    |             1.6 |
| megacap_earnings |             7.8 |
| any_major_event  |            22.7 |

## original rules

|                  | event days, early   | other days, early   | event days, late   | other days, late   |
|:-----------------|:--------------------|:--------------------|:-------------------|:-------------------|
| fomc_day         | +0.78 (1)           | -0.18 (52)          | –                  | -0.12 (39)         |
| fomc_next_day    | +0.23 (2)           | -0.18 (51)          | +0.13 (2)          | -0.13 (37)         |
| macro_830        | -0.66 (7)           | -0.09 (46)          | -0.08 (9)          | -0.13 (30)         |
| opex             | +0.23 (2)           | -0.18 (51)          | -0.27 (2)          | -0.11 (37)         |
| quad_witching    | -1.02 (1)           | -0.15 (52)          | -0.27 (2)          | -0.11 (37)         |
| megacap_earnings | +0.06 (6)           | -0.19 (47)          | +0.25 (3)          | -0.15 (36)         |
| any_major_event  | -0.33 (10)          | -0.12 (43)          | -0.04 (11)         | -0.14 (28)         |

## gap-down reversal

|                  | event days, early   | other days, early   | event days, late   | other days, late   |
|:-----------------|:--------------------|:--------------------|:-------------------|:-------------------|
| fomc_day         | +0.47 (3)           | -0.01 (300)         | +0.30 (3)          | -0.06 (266)        |
| fomc_next_day    | -0.07 (11)          | -0.00 (292)         | -0.72 (8)          | -0.04 (261)        |
| macro_830        | -0.12 (41)          | +0.01 (262)         | -0.09 (48)         | -0.05 (221)        |
| opex             | +0.28 (13)          | -0.02 (290)         | -0.12 (16)         | -0.05 (253)        |
| quad_witching    | +0.73 (6)           | -0.02 (297)         | +0.11 (7)          | -0.06 (262)        |
| megacap_earnings | -0.13 (24)          | +0.01 (279)         | +0.28 (21)         | -0.08 (248)        |
| any_major_event  | -0.08 (55)          | +0.01 (248)         | -0.18 (58)         | -0.02 (211)        |

## every-session candidate

|                  | event days, early   | other days, early   | event days, late   | other days, late   |
|:-----------------|:--------------------|:--------------------|:-------------------|:-------------------|
| fomc_day         | -0.17 (29)          | -0.06 (919)         | -0.13 (28)         | -0.04 (874)        |
| fomc_next_day    | -0.26 (30)          | -0.05 (918)         | +0.08 (30)         | -0.05 (872)        |
| macro_830        | -0.10 (134)         | -0.05 (814)         | -0.11 (188)        | -0.03 (714)        |
| opex             | -0.01 (42)          | -0.06 (906)         | -0.01 (43)         | -0.05 (859)        |
| quad_witching    | +0.41 (15)          | -0.07 (933)         | +0.18 (14)         | -0.05 (888)        |
| megacap_earnings | -0.24 (71)          | -0.05 (877)         | +0.05 (73)         | -0.06 (829)        |
| any_major_event  | -0.15 (188)         | -0.04 (760)         | -0.08 (241)        | -0.03 (661)        |

## Fixed rule: skip / only major-event days (whole period)

|                                                     |   trades |   avg_R |   total_R |      t |
|:----------------------------------------------------|---------:|--------:|----------:|-------:|
| ('original rules', 'all days')                      |       92 |  -0.143 |   -13.144 | -1.405 |
| ('original rules', 'skip any_major_event')          |       71 |  -0.132 |    -9.365 | -1.116 |
| ('original rules', 'only any_major_event')          |       21 |  -0.18  |    -3.778 | -0.892 |
| ('gap-down reversal', 'all days')                   |      572 |  -0.028 |   -16.242 | -0.634 |
| ('gap-down reversal', 'skip any_major_event')       |      459 |  -0.003 |    -1.446 | -0.062 |
| ('gap-down reversal', 'only any_major_event')       |      113 |  -0.131 |   -14.796 | -1.369 |
| ('every-session candidate', 'all days')             |     1850 |  -0.054 |  -100.216 | -2.198 |
| ('every-session candidate', 'skip any_major_event') |     1421 |  -0.036 |   -51.064 | -1.271 |
| ('every-session candidate', 'only any_major_event') |      429 |  -0.115 |   -49.153 | -2.283 |

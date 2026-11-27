# Forward test journal — core portfolio, intraday add-on, fade (shadow)

Sessions logged: 10; add-on signal days: 1; GO decisions: 6; add-on trades: 0, P&L $0; fade shadow signals: 4, avg -0.02R

Does Claude's morning decision separate good add-on days from bad ones? (shadow return 10:00 -> 11:55, traded or not)

| group | add-on signal days | avg shadow return | total |
|---|---:|---:|---:|
| decided GO | 0 | – | – |
| decided NO_GO | 1 | -0.602% | -0.60% |
| all add-on signal days | 1 | -0.602% | -0.60% |

| date       | decision   |   confidence | regime        |   addon_efficiency | addon_signal   |   addon_shadow_ret_% | addon_traded   |   addon_pnl_usd |   core_gross |   core_orders |   core_unfilled | leaps_signal   |   leaps_bought |   leaps_sold |   leaps_open | fade_signal   |   fade_shadow_R | traded   |   paper_pnl_usd |
|:-----------|:-----------|-------------:|:--------------|-------------------:|:---------------|---------------------:|:---------------|----------------:|-------------:|--------------:|----------------:|:---------------|---------------:|-------------:|-------------:|:--------------|----------------:|:---------|----------------:|
| 2026-11-13 | NO_GO      |         0.95 | down/vix15-20 |               0.42 | False          |               nan    | False          |             nan |         0.93 |            13 |               0 |                |              0 |            0 |       nan    | False         |          nan    | False    |             nan |
| 2026-11-16 | GO         |         0.60 | down/vix15-20 |               0.15 | False          |               nan    | False          |             nan |         1.64 |            13 |               0 | False          |              0 |            0 |         0.00 | True          |            0.99 | False    |             nan |
| 2026-11-17 | GO         |         0.55 | down/vix>=20  |               0.09 | False          |               nan    | False          |             nan |       nan    |             0 |               0 |                |              0 |            0 |       nan    | True          |            0.98 | False    |             nan |
| 2026-11-19 | GO         |         0.55 | down/vix>=20  |               0.08 | False          |               nan    | False          |             nan |         1.36 |             2 |               0 | False          |              0 |            0 |         0.00 | False         |          nan    | False    |             nan |
| 2026-11-20 | GO         |         0.50 | down/vix>=20  |               0.19 | False          |               nan    | False          |             nan |         2.00 |             8 |               0 | False          |              0 |            0 |         0.00 | True          |           -1.02 | False    |             nan |
| 2026-11-23 | GO         |         0.45 | down/vix>=20  |               0.12 | False          |               nan    | False          |             nan |         0.92 |             8 |               0 | False          |              0 |            0 |         0.00 | False         |          nan    | False    |             nan |
| 2026-11-24 | NO_GO      |         0.60 | down/vix>=20  |               0.27 | True           |                -0.60 | False          |             nan |         0.92 |             0 |               0 | False          |              0 |            0 |         0.00 | True          |           -1.02 | False    |             nan |
| 2026-11-25 | GO         |         0.50 | down/vix>=20  |               0.02 | False          |               nan    | False          |             nan |         0.92 |             0 |               0 | False          |              0 |            0 |         0.00 | False         |          nan    | False    |             nan |
| 2026-11-26 | NO_GO      |         1.00 | nan           |             nan    |                |               nan    | False          |             nan |       nan    |             0 |               0 |                |              0 |            0 |         0.00 | False         |          nan    | False    |             nan |
| 2026-11-27 | NO_GO      |         0.90 | down/vix>=20  |               0.36 | False          |               nan    | False          |             nan |       nan    |             0 |               0 | False          |              0 |            0 |         0.00 | False         |          nan    | False    |             nan |
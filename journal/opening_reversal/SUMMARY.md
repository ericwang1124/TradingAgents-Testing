# Forward test journal — core portfolio, intraday add-on, fade (shadow)

Sessions logged: 2; add-on signal days: 0; GO decisions: 1; add-on trades: 0, P&L $0; fade shadow signals: 1, avg +0.99R

Does Claude's morning decision separate good add-on days from bad ones? (shadow return 10:00 -> 11:55, traded or not)

| group | add-on signal days | avg shadow return | total |
|---|---:|---:|---:|
| decided GO | 0 | – | – |
| decided NO_GO | 0 | – | – |
| all add-on signal days | 0 | – | – |

| date       | decision   |   confidence | regime        |   addon_efficiency | addon_signal   |   addon_shadow_ret_% | addon_traded   |   addon_pnl_usd |   core_gross |   core_orders |   core_unfilled | leaps_signal   |   leaps_bought |   leaps_sold |   leaps_open | fade_signal   |   fade_shadow_R | traded   |   paper_pnl_usd |
|:-----------|:-----------|-------------:|:--------------|-------------------:|:---------------|---------------------:|:---------------|----------------:|-------------:|--------------:|----------------:|:---------------|---------------:|-------------:|-------------:|:--------------|----------------:|:---------|----------------:|
| 2026-11-13 | NO_GO      |         0.95 | down/vix15-20 |               0.42 | False          |                  nan | False          |             nan |         0.93 |            13 |               0 |                |              0 |            0 |       nan    | False         |          nan    | False    |             nan |
| 2026-11-16 | GO         |         0.60 | down/vix15-20 |               0.15 | False          |                  nan | False          |             nan |         1.64 |            13 |               0 | False          |              0 |            0 |         0.00 | True          |            0.99 | False    |             nan |
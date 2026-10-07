# COT 持仓变化参考结果

10 个实体已用 CFTC 官方 API 与年度 Legacy Futures Only 历史文件逐行核对。首次发布版本的修订链仍未证明，不能据此宣称满足正式 fitting provenance 的首次发布值条件。

| entity_id | 市场代码 | 起始净持仓 | 结束净持仓 | 变化 / 起始 OI（%） | 排名 |
| --- | --- | ---: | ---: | ---: | ---: |
| CORN_CBT | 002602 | 17840 | 136869 | 7.2426077988 | 1 |
| ES_SP500 | 13874A | 22981 | -78894 | -4.6588764916 | 7 |
| EURO_FX | 099741 | -28524 | -56009 | -4.2235297553 | 6 |
| GOLD_CMX | 088691 | 296204 | 250338 | -7.9939347462 | 8 |
| JPY_CME | 097741 | 12771 | -22633 | -17.0754999084 | 10 |
| NATGAS_NYMEX | 023651 | -166185 | -153392 | 0.7777467049 | 4 |
| SILVER_CMX | 084691 | 66355 | 42783 | -14.9888086275 | 9 |
| UST_10Y | 043602 | -848191 | -926603 | -1.6823244793 | 5 |
| UST_2Y | 042601 | -1380910 | -1234646 | 3.2181708809 | 2 |
| WTI_NYMEX | 067651 | 173731 | 200407 | 1.6177783384 | 3 |

计算式：`100 * (end_net - start_net) / start_open_interest`。排名 1 表示向净多头移动幅度最大。分母固定使用 2024-10-22 的 open interest，不能改为结束期或净持仓百分比之差。

[官方 Legacy Futures Only 数据集](https://publicreporting.cftc.gov/Commitments-of-Traders/Legacy-Futures-Only/6dca-aqww)；[年度原始 ZIP](https://www.cftc.gov/files/dea/history/deacot2024.zip)。准确查询 URL 与原始资料 hash 见 sources/cot/downloads.json；复算记录见 sources/cot/verification.json。

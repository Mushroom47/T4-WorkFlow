# Treasury 组本地历史结果参考集

已登记 3 个公开单元的 19 个实体行，全部为 `verified`；`provisional=0`，`unresolved=0`。这些结果用于本地实验与开发核对，不是主办方私有 `outcome` 或参赛预设答案。收益率行采用财政部官方名义 CMT 数据并使用 task 指定起值；拍卖行经原始结果 PDF、TreasuryDirect API、FiscalData API 三处核对。这里没有预测概率、预测区间或评分器隐藏理由。

## 版本与证据

- 官方任务版本：`1c744e1d6725340643a533f436517d72b53ca0e1`。
- 数据文件：`research/treasury.json`；逐项核对和任务 SHA-256：`sources/treasury/verification.json`。
- 原始 XML、API JSON、7 份拍卖结果 PDF 及各自 `*.metadata.json` 均保存在 `sources/treasury/`；元数据含来源 URL、抓取 UTC 时间、字节数及 SHA-256。
- 抓取时间：2026-10-07（UTC）；结构化接口无法确认历史发布时刻时，`sources[].published_at` 使用 null，观测日保留在 `inputs[].date`。

## 收益率变化

计算式：`(official_end_yield_pct - task.start_yield_pct) * 100`，单位 `bps_change`。12 个财政部官方起值均与任务给定起值一致。2024 单元的目录名含 2024-09-18，但实际起点依 prompt 和 cutoff 使用 2024-09-19；终点为 2024-11-06。2022 窗口为 2022-07-28 至 2022-09-20。

| 单元 | 实体 | task 起值 % | 官方起值 % | 官方终值 % | 变化 bps |
|---|---|---:|---:|---:|---:|
| t4-fomc-curve-20220728 | UST10Y | 2.68 | 2.68 | 3.57 | 89 |
| t4-fomc-curve-20220728 | UST2Y | 2.85 | 2.85 | 3.96 | 111 |
| t4-fomc-curve-20220728 | UST30Y | 3.02 | 3.02 | 3.59 | 57 |
| t4-fomc-curve-20220728 | UST3Y | 2.81 | 2.81 | 3.94 | 113 |
| t4-fomc-curve-20220728 | UST5Y | 2.69 | 2.69 | 3.75 | 106 |
| t4-fomc-curve-20220728 | UST7Y | 2.69 | 2.69 | 3.69 | 100 |
| t4-fomc-curve-20240918 | UST10Y | 3.73 | 3.73 | 4.42 | 69 |
| t4-fomc-curve-20240918 | UST2Y | 3.59 | 3.59 | 4.27 | 68 |
| t4-fomc-curve-20240918 | UST30Y | 4.06 | 4.06 | 4.60 | 54 |
| t4-fomc-curve-20240918 | UST3Y | 3.47 | 3.47 | 4.20 | 73 |
| t4-fomc-curve-20240918 | UST5Y | 3.49 | 3.49 | 4.27 | 78 |
| t4-fomc-curve-20240918 | UST7Y | 3.60 | 3.60 | 4.37 | 77 |

官方来源：财政部 [2022 年 XML](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2022)、[2024 年 XML](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value=2024)；[2024 年展示页](https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?field_tdr_date_value=2024&type=daily_treasury_yield_curve)提供起终日期的交叉查看，财政部 [XML 说明](https://home.treasury.gov/policy-issues/financing-the-government/interest-rate-statistics/interest-rate-xml-files)说明数据发布入口。2022 年展示页当前提示旧年份转档案，但官方按年 XML 仍返回完整 249 行，包含所需两个日期；2024 XML 返回完整 250 行。

## 拍卖 bid-to-cover

按拍卖日、期限、新发/续发状态精确匹配，获取唯一 CUSIP；7 次目标均为新发且官方 `reopening=No`。比值使用结果 PDF 脚注 4 与 API 的正式公布值，保留两位小数。PDF 的 Subtotal（包含 FIMA 非竞争投标、排除 SOMA）用于复算；直接用 API 的 totalTendered/totalAccepted 会混入 SOMA，导致错误结果。

| 实体 | 拍卖日 | 期限 | CUSIP | bid-to-cover | 原始结果 |
|---|---|---|---|---:|---|
| AUC_10Y_20241105 | 2024-11-05 | 10-Year | 91282CLW9 | 2.58 | [PDF](https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/R_20241105_2.pdf) |
| AUC_20Y_20241120 | 2024-11-20 | 20-Year | 912810UF3 | 2.34 | [PDF](https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/R_20241120_3.pdf) |
| AUC_2Y_20241125 | 2024-11-25 | 2-Year | 91282CLY5 | 2.77 | [PDF](https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/R_20241125_3.pdf) |
| AUC_30Y_20241106 | 2024-11-06 | 30-Year | 912810UE6 | 2.64 | [PDF](https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/R_20241106_2.pdf) |
| AUC_3Y_20241104 | 2024-11-04 | 3-Year | 91282CLX7 | 2.60 | [PDF](https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/R_20241104_3.pdf) |
| AUC_5Y_20241126 | 2024-11-26 | 5-Year | 91282CMA6 | 2.43 | [PDF](https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/R_20241126_4.pdf) |
| AUC_7Y_20241127 | 2024-11-27 | 7-Year | 91282CLZ2 | 2.71 | [PDF](https://www.treasurydirect.gov/instit/annceresult/press/preanre/2024/R_20241127_3.pdf) |

官方接口：TreasuryDirect `TA_WS/securities/search?format=json&auctionDate=YYYY-MM-DD`；FiscalData `v1/accounting/od/auctions_query` 使用 `auction_date` 的 2024 年 11 月范围过滤。FiscalData 返回 36 条、1 页，7 个目标均唯一且与 TreasuryDirect 的比值一致。[TreasuryDirect Auction Query](https://www.treasurydirect.gov/auctions/auction-query/)提供官方历史查询入口。各实体 JSON 保存精确查询 URL 和字段定位。

## 自查与边界

- 19 行和 19 个 `(task_id, entity_id)` 唯一键，与三个 task 的 entities 精确一致。
- 19 个结果均为有限数值；所有 `reference_label=null`，与回归 target.type 一致。
- 12/12 收益率起值一致，7/7 拍卖身份和两接口比值一致，7/7 Subtotal 比值四舍五入后与正式公布值一致。
- 这些数据说明公开历史实现结果；没有主办方私有真值、隐藏解析程序和生产 NLI judge，因此 `verified` 表示公开来源与定义核对完成，不表示已经与私有 outcome 一致性认证。
- 原始证据是研究资料；不应直接作为正式程序在 cutoff 后访问的输入或内置 task-answer lookup。

## 0.1.1收益率历史版本补证

12个实体的24起止端点已逐日查三个相邻ALFRED vintage，全部与task/XML一致，bps差异0；历史CSV和完整日期边界见[补证报告](../sources/yield-vintages/yield-vintage-report.md)。ALFRED最早测试可见日不等于Treasury全球首次发布时点，未据此宣称正式首发链完整。合并JSONL source/notes已更新。

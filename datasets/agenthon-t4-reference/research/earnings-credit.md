# EPS、信用事件与财报后市场反应：公开历史事实参考

本文件服务于本地实验和开发验证。它依据公开历史披露/公开行情数据重建结果，不是组织者持有的官方 outcome，也不表示获准将事后信息输入正式预测 Agent。生成日期：2026-10-07。

覆盖 5 个公开 task、26 个实体行：18 行 `verified`，8 行 `provisional`，0 行 `unresolved`。其中 Amgen 的季度事实已核实但与题面 resolution_date 冲突；4 个 `no_event` 和 3 个市场反应保留 provisional。信用标签不转换为概率；其 `reference_value` 全部为 null。

JSON 的分类 EPS `reference_value` 是实际单季 GAAP diluted EPS（USD/share）；银行回归值为按题面 baseline 计算的同比增长百分数；市场反应数值为公司收益减 SPY 收益的百分点差，按异常收益百分数报告。

| task_id | entity_id | 历史参考标签 | reference_value | 单位 | 状态 |
|---|---|---|---:|---|---|
| t4-EXAMPLE-eps-beat | AAPL | inline | 1.53 | USD/share | verified |
| t4-eps-yoy-2023Q2-mixed | AMD | down | 0.02 | USD/share | verified |
| t4-eps-yoy-2023Q2-mixed | AMGN | up | 2.57 | USD/share | provisional |
| t4-eps-yoy-2023Q2-mixed | DOW | down | 0.68 | USD/share | verified |
| t4-eps-yoy-2023Q2-mixed | HON | up | 2.22 | USD/share | verified |
| t4-eps-yoy-2023Q2-mixed | IBM | up | 1.72 | USD/share | verified |
| t4-eps-yoy-2023Q2-mixed | TMO | down | 3.51 | USD/share | verified |
| t4-eps-growth-2024Q3-banks | BAC | — | -10 | percent | verified |
| t4-eps-growth-2024Q3-banks | C | — | -7.3619631902 | percent | verified |
| t4-eps-growth-2024Q3-banks | GS | — | 53.5648994516 | percent | verified |
| t4-eps-growth-2024Q3-banks | JPM | — | 0.9237875289 | percent | verified |
| t4-eps-growth-2024Q3-banks | MS | — | 36.231884058 | percent | verified |
| t4-eps-growth-2024Q3-banks | PNC | — | -3.0555555556 | percent | verified |
| t4-eps-growth-2024Q3-banks | USB | — | 13.1868131868 | percent | verified |
| t4-eps-growth-2024Q3-banks | WFC | — | -4.0540540541 | percent | verified |
| t4-credit-event-2023 | BBBY | credit_event | null | label | verified |
| t4-credit-event-2023 | BBY | no_event | null | label | provisional |
| t4-credit-event-2023 | M | no_event | null | label | provisional |
| t4-credit-event-2023 | ODFL | no_event | null | label | provisional |
| t4-credit-event-2023 | RAD | credit_event | null | label | verified |
| t4-credit-event-2023 | WBA | no_event | null | label | provisional |
| t4-credit-event-2023 | WE | credit_event | null | label | verified |
| t4-credit-event-2023 | YELL | credit_event | null | label | verified |
| t4-postearn-20240201-megacap | AAPL | negative_reaction | -1.593250779 | percent | provisional |
| t4-postearn-20240201-megacap | AMZN | positive_reaction | 6.8139107587 | percent | provisional |
| t4-postearn-20240201-megacap | META | positive_reaction | 19.2649061048 | percent | provisional |

## EPS 口径与原始来源定位

单季数值均与 SEC `us-gaap:EarningsPerShareDiluted` 的原始季度期间、首次该季 10-Q accession 和 filed 日期交叉核对。没有使用半年/九个月累计值、basic EPS 或 adjusted EPS。银行按 `(actual_eps − task_prior_year_q_eps) / task_prior_year_q_eps × 100` 计算，8 个基准全部为正数，本组没有负 EPS baseline 的特殊分支。题面 baseline 保持原值。

- **t4-EXAMPLE-eps-beat / AAPL**：取 Apple FY2024 第二季度 GAAP diluted EPS 1.53，与 task.json 给定 consensus 1.50 比较。beat 严格大于 1.575，miss 严格小于 1.425；1.53 位于区间内，因此 inline。reference_value 是实际季度 EPS，不是预测值。 原始来源：[ Apple reports second quarter results ](https://www.apple.com/newsroom/2024/05/apple-reports-second-quarter-results/)，发布 2024-05-02；定位：正文首段：FY2024 Q2、财季截至 2024-03-30、diluted EPS 1.53；不要用 FY2024 Q1 的 2.18。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000320193/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2023-12-31, end=2024-03-30, val=1.53；首次季度 10-Q accession=0000320193-24-000069，filed=2024-05-03。完整单指标 raw 为 sec-eps-AAPL-concept.raw.json，SHA-256=d58cd0fce2baed8be20b7b6587917b03bb46c08fc0b527d53a4867cab9317acf；可直接回读复算。
- **t4-eps-yoy-2023Q2-mixed / AMD**：取对应 June-2023 财季的单季 GAAP diluted EPS 0.02，按 task.json 给定 prior_year_q_eps 0.27 直接比较，得到 down。reference_value 是实际季度 EPS；相等时题面无标签，本组未出现相等值。 原始来源：[ AMD Reports Second Quarter 2023 Financial Results ](https://www.amd.com/en/newsroom/press-releases/2023-8-1-amd-reports-second-quarter-2023-financial-results.html)，发布 2023-08-01；定位：GAAP Quarterly Financial Results 表，Q2 2023 / Q2 2022，Diluted earnings per share：0.02 / 0.27；non-GAAP 0.58 不适用。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000002488/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2023-04-02, end=2023-07-01, val=0.02；首次季度 10-Q accession=0000002488-23-000139，filed=2023-08-02。完整单指标 raw 为 sec-eps-AMD-concept.raw.json，SHA-256=15436f232b8f49ef33d8cebf6ba7c4696048ef093290ef5f68ef48cb65e5c53a；可直接回读复算。 prior baseline 的原始季度观察值：start=2022-03-27, end=2022-06-25, val=0.27, accession=0000002488-22-000123, filed=2022-08-03。
  题面写 three months ended 2023-06-30；公司对应 June-2023 财季实际截至 2023-07-01。按相应 FY2023 Q2 单季值对照，保留此一日财历差异。
- **t4-eps-yoy-2023Q2-mixed / AMGN**：取对应 June-2023 财季的单季 GAAP diluted EPS 2.57，按 task.json 给定 prior_year_q_eps 2.45 直接比较，得到 up。reference_value 是实际季度 EPS；相等时题面无标签，本组未出现相等值。 原始来源：[ AMGEN REPORTS SECOND QUARTER FINANCIAL RESULTS ](https://www.amgen.com/newsroom/press-releases/2023/08/amgen-reports-second-quarter-financial-results)，发布 2023-08-03；定位：发布时间 2023-08-03；GAAP EPS 首段及 GAAP/Non-GAAP reconciliation，Three Months Ended June 30：2.57 / 2.45；六个月 7.86 不适用。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000318154/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2023-04-01, end=2023-06-30, val=2.57；首次季度 10-Q accession=0000318154-23-000053，filed=2023-08-04。完整单指标 raw 为 sec-eps-AMGN-concept.raw.json，SHA-256=44fda87915cfe7d797eb3d600fde86258fb8098832c87d395397cf4126600c60；可直接回读复算。 prior baseline 的原始季度观察值：start=2022-04-01, end=2022-06-30, val=2.45, accession=0000318154-22-000041, filed=2022-08-05。
  季度 EPS 2.57 的原始披露已核实，但公告实际在 2023-08-03，10-Q 在 2023-08-04；均晚于 task resolution_date 2023-08-02。题面 expected_report_date 2023-08-01 与真实日期不一致，历史季度比较可用，官方该截止日如何定 outcome 未知。
- **t4-eps-yoy-2023Q2-mixed / DOW**：取对应 June-2023 财季的单季 GAAP diluted EPS 0.68，按 task.json 给定 prior_year_q_eps 2.26 直接比较，得到 down。reference_value 是实际季度 EPS；相等时题面无标签，本组未出现相等值。 原始来源：[ Dow reports second quarter 2023 results ](https://investors.dow.com/en/news/news-details/2023/Dow-reports-second-quarter-2023-results/default.aspx)，发布 2023-07-25；定位：Consolidated Statements of Income，Three Months Ended June 30 2023/2022，Earnings per common share — diluted：0.68 / 2.26；operating EPS 0.75 不适用。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0001751788/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2023-04-01, end=2023-06-30, val=0.68；首次季度 10-Q accession=0001751788-23-000128，filed=2023-07-26。完整单指标 raw 为 sec-eps-DOW-concept.raw.json，SHA-256=a30ac9e0fba86bc51b2b43d386bbb5e23e4091c175514318ca03cf59c99b35a3；可直接回读复算。 prior baseline 的原始季度观察值：start=2022-04-01, end=2022-06-30, val=2.26, accession=0001751788-22-000123, filed=2022-07-22。
- **t4-eps-yoy-2023Q2-mixed / HON**：取对应 June-2023 财季的单季 GAAP diluted EPS 2.22，按 task.json 给定 prior_year_q_eps 1.84 直接比较，得到 up。reference_value 是实际季度 EPS；相等时题面无标签，本组未出现相等值。 原始来源：[ Honeywell Delivers Strong Second Quarter Results And Raises Full Year Sales, Segment Margin, And Adjusted EPS Guidance ](https://www.honeywell.com/us/en/news/press-releases/2023/07/honeywell-delivers-strong-second-quarter-results-and-raises-full-year-sales-segment-margin-and-adjusted-eps-guidance)，发布 2023-07-27；定位：Summary Financial Results：GAAP Earnings Per Share 2.22 / 1.84；adjusted EPS 2.23 / 2.10 不适用。Diluted 属性另由 SEC 原始季度 XBRL 核对。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000773840/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2023-04-01, end=2023-06-30, val=2.22；首次季度 10-Q accession=0000773840-23-000073，filed=2023-07-27。完整单指标 raw 为 sec-eps-HON-concept.raw.json，SHA-256=91667ff55623f86cc5718b4d45147e694a9cd3ee0815d4b04e573acc0876cf71；可直接回读复算。 prior baseline 的原始季度观察值：start=2022-04-01, end=2022-06-30, val=1.84, accession=0000773840-22-000054, filed=2022-07-28。
- **t4-eps-yoy-2023Q2-mixed / IBM**：取对应 June-2023 财季的单季 GAAP diluted EPS 1.72，按 task.json 给定 prior_year_q_eps 1.53 直接比较，得到 up。reference_value 是实际季度 EPS；相等时题面无标签，本组未出现相等值。 原始来源：[ IBM Form 10-Q, quarter ended June 30, 2023 ](https://www.sec.gov/Archives/edgar/data/51143/000005114323000021/ibm-20230630.htm)，发布 2023-07-25；定位：Note 7 — Earnings Per Share of Common Stock，第 19 页；For the three months ended June 30，Assuming dilution — Total：2023 1.72 / 2022 1.53；2022 continuing operations 1.61 不能替代题面基准。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000051143/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2023-04-01, end=2023-06-30, val=1.72；首次季度 10-Q accession=0000051143-23-000021，filed=2023-07-25。完整单指标 raw 为 sec-eps-IBM-concept.raw.json，SHA-256=7b81dcc0a49349da6e8b4aee646ed9e5189d2e7d33dee9ba6beacd62dcc9dcc7；可直接回读复算。 prior baseline 的原始季度观察值：start=2022-04-01, end=2022-06-30, val=1.53, accession=0001558370-22-010985, filed=2022-07-25。
  使用含 discontinued operations 的 Total assuming dilution；题面 2022 基准 1.53 与原始 Note 7 一致，不能用 continuing operations 的 1.61 改写 baseline。
- **t4-eps-yoy-2023Q2-mixed / TMO**：取对应 June-2023 财季的单季 GAAP diluted EPS 3.51，按 task.json 给定 prior_year_q_eps 4.22 直接比较，得到 down。reference_value 是实际季度 EPS；相等时题面无标签，本组未出现相等值。 原始来源：[ Thermo Fisher Scientific Reports Second Quarter 2023 Results ](https://ir.thermofisher.com/investors/news-events/news/news-details/2023/Thermo-Fisher-Scientific-Reports-Second-Quarter-2023-Results/)，发布 2023-07-26；定位：GAAP Earnings Results 和 Condensed Consolidated Statement of Income：Diluted EPS 3.51 / 4.22，季度实际截至 2023-07-01；adjusted 5.15 不适用。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000097745/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2023-04-02, end=2023-07-01, val=3.51；首次季度 10-Q accession=0000097745-23-000059，filed=2023-08-04。完整单指标 raw 为 sec-eps-TMO-concept.raw.json，SHA-256=447eae05d7460d87c66be24b882e5194361c822d539ddd1ec86aa8e64eb08d96；可直接回读复算。 prior baseline 的原始季度观察值：start=2022-04-03, end=2022-07-02, val=4.22, accession=0000097745-22-000047, filed=2022-08-05。
  题面写 three months ended 2023-06-30；公司对应 June-2023 财季实际截至 2023-07-01。按相应 FY2023 Q2 单季值对照，保留此一日财历差异。
- **t4-eps-growth-2024Q3-banks / BAC**：取截至 2024-09-30 三个月 GAAP diluted EPS 0.81，使用 task.json 给定基准 0.9，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ Bank of America 3Q24 earnings presentation, Exhibit 99.2 ](https://www.sec.gov/Archives/edgar/data/70858/000007085824000266/bac09302024ex992.htm)，发布 2024-10-15；定位：第 2 页 / Summary Income Statement，3Q24 / 3Q23，Diluted earnings per share：0.81 / 0.90。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000070858/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=0.81；首次季度 10-Q accession=0000070858-24-000280，filed=2024-10-29。完整单指标 raw 为 sec-eps-BAC-concept.raw.json，SHA-256=2133ba4c4365fb48817dd9557c0244519a99aced91693b3e6372c39f706da786；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=0.9, accession=0000070858-23-000272, filed=2023-10-31。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。
- **t4-eps-growth-2024Q3-banks / C**：取截至 2024-09-30 三个月 GAAP diluted EPS 1.51，使用 task.json 给定基准 1.63，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ Citigroup Reports Third Quarter 2024 Results ](https://www.citigroup.com/rcs/citigpa/storage/public/Earnings/Q32024/2024pr-qtr3rslt.pdf)，发布 2024-10-15；定位：PDF 第 1 页，2024-10-15，EPS 1.51 对比 3Q23 1.63；Diluted 属性由 SEC 原始季度 XBRL 核对。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000831001/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=1.51；首次季度 10-Q accession=0000831001-24-000134，filed=2024-11-07。完整单指标 raw 为 sec-eps-C-concept.raw.json，SHA-256=23820b28db5ee74137fd4703a7baa9ec4e2d51065391919d7da75d35651add13；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=1.63, accession=0000831001-23-000132, filed=2023-11-03。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。
- **t4-eps-growth-2024Q3-banks / GS**：取截至 2024-09-30 三个月 GAAP diluted EPS 8.4，使用 task.json 给定基准 5.47，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ Goldman Sachs Reports 2024 Third Quarter Earnings Results ](https://www.goldmansachs.com/pressroom/press-releases/2024/2024-10-15-q3-results)，发布 2024-10-15；定位：公告首段，quarter ended September 30, 2024，diluted EPS 8.40；同期 earnings PDF 第 1 页对照 3Q23 5.47。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000886982/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=8.4；首次季度 10-Q accession=0000886982-24-000025，filed=2024-11-04。完整单指标 raw 为 sec-eps-GS-concept.raw.json，SHA-256=b8c3d05e883361ebd8543b3dfce7c0f40fda35a90cb1f604416f352a871b64db；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=5.47, accession=0000886982-23-000011, filed=2023-11-03。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。
- **t4-eps-growth-2024Q3-banks / JPM**：取截至 2024-09-30 三个月 GAAP diluted EPS 4.37，使用 task.json 给定基准 4.33，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ JPMorgan Chase Reports Third-Quarter 2024 Financial Results ](https://www.sec.gov/Archives/edgar/data/19617/000001961724000555/a3q24erfexhibit991narrative.htm)，发布 2024-10-11；定位：2024-10-11 Exhibit 99.1，NET INCOME OF $12.9 BILLION / $4.37 PER SHARE；Diluted 属性与 SEC XBRL 以及 earnings supplement Diluted EPS 行核对。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000019617/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=4.37；首次季度 10-Q accession=0000019617-24-000611，filed=2024-10-30。完整单指标 raw 为 sec-eps-JPM-concept.raw.json，SHA-256=39a48e8fed3c70d6a3adf5fd6f4fa529e10d1849dc918cfee2650b0d69cb7fc8；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=4.33, accession=0000019617-23-000524, filed=2023-11-01。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。
- **t4-eps-growth-2024Q3-banks / MS**：取截至 2024-09-30 三个月 GAAP diluted EPS 1.88，使用 task.json 给定基准 1.38，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ Morgan Stanley Reports Third Quarter 2024 ](https://www.sec.gov/Archives/edgar/data/895421/000089542124000484/a3q24msearningsrelease.htm)，发布 2024-10-16；定位：首段及 Financial Summary：diluted EPS 1.88 对比 1.38，Three Months Ended September 30 2024/2023。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000895421/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=1.88；首次季度 10-Q accession=0000895421-24-000491，filed=2024-11-04。完整单指标 raw 为 sec-eps-MS-concept.raw.json，SHA-256=ed8de86db84b91eca61826bfd35604582ccd31ef5be4b51eac9dd24f69249358；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=1.38, accession=0000895421-23-000441, filed=2023-11-03。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。
- **t4-eps-growth-2024Q3-banks / PNC**：取截至 2024-09-30 三个月 GAAP diluted EPS 3.49，使用 task.json 给定基准 3.6，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ PNC Reports Third Quarter 2024 Net Income of $1.5 Billion, $3.49 Diluted EPS ](https://investor.pnc.com/news-events/financial-press-releases/detail/639/pnc-reports-third-quarter-2024-net-income-of-1-5-billion-3-49-diluted-eps)，发布 2024-10-15；定位：Financial Results Summary，列 3Q24 / 2Q24 / 3Q23，Diluted earnings per common share：3.49 / 3.39 / 3.60；基准使用 3Q23。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000713676/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=3.49；首次季度 10-Q accession=0000713676-24-000081，filed=2024-11-01。完整单指标 raw 为 sec-eps-PNC-concept.raw.json，SHA-256=f92fe3a631659ab0423319adcdd8fb7fb4fe26cce69b93758012a4e370683375；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=3.6, accession=0000713676-23-000079, filed=2023-11-02。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。
- **t4-eps-growth-2024Q3-banks / USB**：取截至 2024-09-30 三个月 GAAP diluted EPS 1.03，使用 task.json 给定基准 0.91，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ U.S. Bancorp Reports Third Quarter 2024 Results ](https://www.sec.gov/Archives/edgar/data/36104/000003610424000062/a3q24earningsrelease.htm)，发布 2024-10-16；定位：GAAP diluted EPS 行，3Q24 1.03 / 3Q23 0.91；剔除 notable items 后的 3Q23 1.05 不适用。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000036104/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=1.03；首次季度 10-Q accession=0000036104-24-000072，filed=2024-11-05。完整单指标 raw 为 sec-eps-USB-concept.raw.json，SHA-256=562214f55ce0ec284e2d94246314b6a35b853f0d8fe75e520c6bf003e028ede1；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=0.91, accession=0001193125-23-268341, filed=2023-11-01。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。
  3Q23 0.91 是 GAAP diluted EPS；剔除 notable items 的 1.05 属调整值，不替代任务基准。
- **t4-eps-growth-2024Q3-banks / WFC**：取截至 2024-09-30 三个月 GAAP diluted EPS 1.42，使用 task.json 给定基准 1.48，计算 (actual_eps - prior_year_q_eps) / prior_year_q_eps × 100。本组全部基准为正数；输出百分数而非比例。 原始来源：[ Wells Fargo Reports Third Quarter 2024 Financial Results ](https://www.sec.gov/Archives/edgar/data/72971/000007297124000218/wfc3qer10-11x24ex991xrelea.htm)，发布 2024-10-11；定位：Financial Results，Quarter ended Sept 30 2024/2023，Diluted earnings per common share：1.42 / 1.48。 [SEC XBRL 交叉核对](https://data.sec.gov/api/xbrl/companyconcept/CIK0000072971/us-gaap/EarningsPerShareDiluted.json)：us-gaap / EarningsPerShareDiluted / USD/shares：start=2024-07-01, end=2024-09-30, val=1.42；首次季度 10-Q accession=0000072971-24-000243，filed=2024-10-31。完整单指标 raw 为 sec-eps-WFC-concept.raw.json，SHA-256=1e20e27e2c96f370b20dabf8d8cc6e1af5ec2904899c9b627fbe47866b92eaa6；可直接回读复算。 prior baseline 的原始季度观察值：start=2023-07-01, end=2023-09-30, val=1.48, accession=0000072971-23-000170, filed=2023-10-31。
  首次业绩公告在 2024-10-11 至 2024-10-16，早于 resolution_date 2024-10-24；之后的 10-Q XBRL 仅用于交叉核对，没有把申报日误记为首次公告日。

## 信用事件窗口及负事件限制

窗口为 **(2023-03-31, 2024-03-31]**。申请 Chapter 11/7、付款违约或评级机构认定的 distressed exchange 任一项成立即可判定 `credit_event`。法院申请日与 SEC 提交日分开记录。`reference_value=null`，历史分类不代表当时预测概率。

**BBBY：credit_event / verified**。核实 Chapter 11 申请日期落在 (2023-03-31, 2024-03-31] 内；任一合格事件足以确定 credit_event。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [Bed Bath & Beyond Inc. Files Voluntary Chapter 11 Petitions](https://www.sec.gov/Archives/edgar/data/886158/000119312523111754/d465247dex991.htm)（2023-04-23）：Exhibit 99.1 公告首段：2023-04-23，公司与部分子公司在美国新泽西州破产法院自愿申请 Chapter 11。

**BBY：no_event / provisional**。以完整窗口的 SEC 申报目录核对破产/违约相关 Item，再结合跨越窗口的年度及季度债务、授信、偿债或 covenant 披露，暂记 no_event。证据是连续公开披露与窗口检查的组合；未穷尽法院案卷及全部评级机构的 distressed exchange 记录，不能升级 verified。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [Best Buy Form 10-K, fiscal year ended February 3, 2024](https://www.sec.gov/Archives/edgar/data/764478/000076447824000010/bby-20240203x10k.htm)（2024-03-15）：MD&A — Sources of Liquidity / debt facility and credit ratings：2024-02-03 所有 financial covenants 合规；截至 2024-03-13 信用评级与上一年相同，S&P BBB+/Stable、Moody's A3/Stable；Note 8 — Debt 列示 2028/2030 notes。
- [Best Buy Form 10-Q, quarter ended May 4, 2024](https://www.sec.gov/Archives/edgar/data/764478/000076447824000022/bby-20240504x10q.htm)（2024-06-07）：Note 6 — Debt：截至 2024-05-04、2024-02-03、2023-04-29 五年循环授信未提款；2028/2030 notes 500/650 百万美元本金持续列示；该季度覆盖信用窗口尾部 2024-02-04 至 2024-03-31。
- [SEC submissions history: BBY](https://data.sec.gov/submissions/CIK0000764478.json)（动态公开数据集，首次版本日期未知）：核对 (2023-03-31, 2024-03-31] 内 15 份 8-K/8-K/A/10-K/10-Q 的 filingDate、form、items，未发现 Item 1.03 或 2.04；含窗口后季度的 18 份记录及 archive feed 已保存。元数据检查不能排除未披露/非重大事件。
此处的连续申报与期末 covenant/债务余额证据尚未穷尽法院案卷及所有评级机构的事件历史，不能宣称全面证明没有事件。继续核查路径：相应 SEC accession 原文、破产法院案卷、S&P/Moody's/Fitch 完整窗口违约与 distressed-exchange 台账。

**M：no_event / provisional**。以完整窗口的 SEC 申报目录核对破产/违约相关 Item，再结合跨越窗口的年度及季度债务、授信、偿债或 covenant 披露，暂记 no_event。证据是连续公开披露与窗口检查的组合；未穷尽法院案卷及全部评级机构的 distressed exchange 记录，不能升级 verified。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [Macy's Form 10-K, fiscal year ended February 3, 2024](https://www.sec.gov/Archives/edgar/data/794367/000162828024012734/m-20240203.htm)（2024-03-22）：Note 6 — Financing Activities，第 58 页 / 2023 Debt Financing Activities：除 ABL 借款外，FY2023 未发生其他重大债务融资活动；截至 2024-02-03 senior notes/debentures 继续列示。 第 29 页 Credit rating and outlook：截至 2024-02-03 Moody's Ba1、S&P BB+、Fitch BBB-，三者均 Stable；现金流补充信息列 FY2023 实付利息 157 百万美元。
- [Macy's Form 10-Q, quarter ended May 4, 2024](https://www.sec.gov/Archives/edgar/data/794367/000162828024025853/m-20240504.htm)（2024-05-30）：Note 4 — Financing Activities：截至 2024-05-04 的 13 周，除资本租赁外未借入或偿还债务；Debt Transactions：senior unsecured notes/debentures 本金在 2024-02-03 和 2024-05-04 均为 3,007 百万美元。季度涵盖 2024-03-31。
- [SEC submissions history: M](https://data.sec.gov/submissions/CIK0000794367.json)（动态公开数据集，首次版本日期未知）：核对 (2023-03-31, 2024-03-31] 内 14 份 8-K/8-K/A/10-K/10-Q 的 filingDate、form、items，未发现 Item 1.03 或 2.04；含窗口后季度的 18 份记录及 archive feed 已保存。元数据检查不能排除未披露/非重大事件。
此处的连续申报与期末 covenant/债务余额证据尚未穷尽法院案卷及所有评级机构的事件历史，不能宣称全面证明没有事件。继续核查路径：相应 SEC accession 原文、破产法院案卷、S&P/Moody's/Fitch 完整窗口违约与 distressed-exchange 台账。

**ODFL：no_event / provisional**。以完整窗口的 SEC 申报目录核对破产/违约相关 Item，再结合跨越窗口的年度及季度债务、授信、偿债或 covenant 披露，暂记 no_event。证据是连续公开披露与窗口检查的组合；未穷尽法院案卷及全部评级机构的 distressed exchange 记录，不能升级 verified。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [Old Dominion Freight Line Form 10-K, year ended December 31, 2023](https://www.sec.gov/Archives/edgar/data/878927/000095017024020176/odfl-20231231.htm)（2024-02-26）：MD&A — General Debt Provisions：截至 2023-12-31 期间所有债务 covenants 合规；Long-Term Debt：2023-05-04 按期偿还 20 百万美元 Series B notes 本金，余 80 百万美元。 现金流补充表列 FY2023 实付利息 3.484 百万美元，债务本金付款 20 百万美元。
- [Old Dominion Freight Line Form 10-Q, quarter ended March 31, 2024](https://www.sec.gov/Archives/edgar/data/878927/000095017024054284/odfl-20240331.htm)（2024-05-07）：MD&A — General Debt Provisions，第 14 页：截至 2024-03-31 期间所有 outstanding debt instruments covenants 合规；Series B notes 余 80 百万美元，循环授信未提款。该季期末恰为完整窗口终点。
- [SEC submissions history: ODFL](https://data.sec.gov/submissions/CIK0000878927.json)（动态公开数据集，首次版本日期未知）：核对 (2023-03-31, 2024-03-31] 内 21 份 8-K/8-K/A/10-K/10-Q 的 filingDate、form、items，未发现 Item 1.03 或 2.04；含窗口后季度的 25 份记录及 archive feed 已保存。元数据检查不能排除未披露/非重大事件。
此处的连续申报与期末 covenant/债务余额证据尚未穷尽法院案卷及所有评级机构的事件历史，不能宣称全面证明没有事件。继续核查路径：相应 SEC accession 原文、破产法院案卷、S&P/Moody's/Fitch 完整窗口违约与 distressed-exchange 台账。

**RAD：credit_event / verified**。核实 Chapter 11 申请日期落在 (2023-03-31, 2024-03-31] 内；任一合格事件足以确定 credit_event。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [Rite Aid Corporation Form 8-K/A, report date October 15, 2023](https://www.sec.gov/Archives/edgar/data/84129/000110465923109413/tm2328535d1_8ka.htm)（2023-10-16）：Item 1.03 Bankruptcy or Receivership：2023-10-15 公司与指定子公司向美国新泽西州破产法院提交 Chapter 11 petitions。该 8-K/A 于 10-16 提交，修订附件不改变事件日期。

**WBA：no_event / provisional**。以完整窗口的 SEC 申报目录核对破产/违约相关 Item，再结合跨越窗口的年度及季度债务、授信、偿债或 covenant 披露，暂记 no_event。证据是连续公开披露与窗口检查的组合；未穷尽法院案卷及全部评级机构的 distressed exchange 记录，不能升级 verified。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [Walgreens Boots Alliance Form 10-K, year ended August 31, 2023](https://www.sec.gov/Archives/edgar/data/1618921/000161892123000062/wba-20230831.htm)（2023-10-12）：Note 8 — Debt / Debt covenants、MD&A Liquidity：截至 2023-08-31 所有 applicable financial covenants 合规，并列示 FY2023 借款、偿债、授信；完整年度覆盖信用窗口前半段。
- [Walgreens Boots Alliance Form 10-Q, quarter ended February 29, 2024](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000035/wba-20240229.htm)（2024-03-28）：Note 7 — Debt / Debt covenants：截至 2024-02-29 财务 covenants 合规；Credit ratings 披露 October 2023 S&P 降至 BBB-、December 2023 Moody's 降至 Ba2。评级下调本身不属于题面信用事件。 截至 2024-02-29 六个月实付利息 301 百万美元。
- [Walgreens Boots Alliance Form 10-Q, quarter ended May 31, 2024](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000065/wba-20240531.htm)（2024-06-27）：Note 7 — Debt / Debt covenants：截至 2024-05-31 所有 applicable financial covenants 合规；Interest：截至该日九个月实际支付利息 460 百万美元；Credit ratings 为 S&P BBB-/Negative、Moody's Ba2/Stable。该季覆盖 2024-03-31 窗口尾部。
- [SEC submissions history: WBA](https://data.sec.gov/submissions/CIK0001618921.json)（动态公开数据集，首次版本日期未知）：核对 (2023-03-31, 2024-03-31] 内 20 份 8-K/8-K/A/10-K/10-Q 的 filingDate、form、items，未发现 Item 1.03 或 2.04；含窗口后季度的 23 份记录及 archive feed 已保存。元数据检查不能排除未披露/非重大事件。
此处的连续申报与期末 covenant/债务余额证据尚未穷尽法院案卷及所有评级机构的事件历史，不能宣称全面证明没有事件。继续核查路径：相应 SEC accession 原文、破产法院案卷、S&P/Moody's/Fitch 完整窗口违约与 distressed-exchange 台账。

**WE：credit_event / verified**。核实 Chapter 11 申请日期落在 (2023-03-31, 2024-03-31] 内；任一合格事件足以确定 credit_event。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [WeWork Inc. Form 8-K, report date November 6, 2023](https://www.sec.gov/Archives/edgar/data/1813756/000119312523271902/d522028d8k.htm)（2023-11-07）：Item 1.03 Bankruptcy or Receivership：2023-11-06 公司与若干直接/间接子公司在美国新泽西州破产法院申请 Chapter 11。

**YELL：credit_event / verified**。核实 Chapter 11 申请日期落在 (2023-03-31, 2024-03-31] 内；任一合格事件足以确定 credit_event。reference_value 留空；信用事件历史标签不转换为预测概率或回归数值。

- [Yellow Corporation Form 8-K, report date August 6, 2023](https://www.sec.gov/Archives/edgar/data/716006/000119312523204370/d483482d8k.htm)（2023-08-07）：Item 1.03 Bankruptcy or Receivership：2023-08-06 公司与若干子公司在美国特拉华州破产法院申请 Chapter 11。Item 2.04 另披露由破产导致的债务违约/加速。

## 股价窗口、数据版本与 total return

Yahoo Chart 请求的 `period1=1706745600` 为 2024-02-01 00:00 UTC，`period2=1707091200` 为 2024-02-05 00:00 UTC（右端不含），`interval=1d`，同时请求 `events=div,splits,capitalGains`。返回 timestamp 为 1706797800、1706884200，按 `America/New_York` 对应 2 月 1 日、2 月 2 日。每个响应仅有这两个交易日，未返回窗口事件。原始响应 bytes 及 SHA-256 均已保存。

价格 series 的浮点尾数先规范到美分；没有使用题面给出的 1 月 31 日价格。SPY 同窗口收盘价为 489.20 → 494.35，同期收益为 **1.0527391660%**。按无窗口除息/拆股/分配事件计算收盘收益，并用当前历史 adjusted-close 比值交叉检查。

| 公司 | 2/1 close | 2/2 close | 公司收益 % | 异常收益 % | adjusted-close 异常 % | 标签 |
|---|---:|---:|---:|---:|---:|---|
| AAPL | 186.86 | 185.85 | -0.5405116130 | -1.5932507790 | -1.5932471530 | negative_reaction |
| AMZN | 159.28 | 171.81 | 7.8666499247 | 6.8139107587 | 6.8139210713 | positive_reaction |
| META | 394.78 | 474.99 | 20.3176452708 | 19.2649061048 | 19.2649089193 | positive_reaction |

三条标签在 close / adjusted-close 两种重算下相同，差异小于 0.000011 个百分点。数据抓取于 2026-10-07；`published_at=null` 表示无法证实该历史数据版本首次发布时间。它是当前公开 vendor 数据快照。total-return 与 close-return 的等同仍依赖窗口事件记录，交易所收盘与完整公司行动台账的独立二次核对尚未完成，因此保留 provisional。

- **AAPL**：[ Yahoo Finance Chart historical daily dataset: AAPL ](https://query1.finance.yahoo.com/v8/finance/chart/AAPL?period1=1706745600&period2=1707091200&interval=1d&events=div%2Csplits%2CcapitalGains)；定位：chart.result[0]：timestamp 按 exchangeTimezoneName=America/New_York 转为 2024-02-01、2024-02-02；indicators.quote[0].close 与 indicators.adjclose[0].adjclose 对应两个交易日；events=div,splits,capitalGains 的请求未返回窗口事件。
- **AAPL**：[ Yahoo Finance Chart historical daily dataset: SPY ](https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1=1706745600&period2=1707091200&interval=1d&events=div%2Csplits%2CcapitalGains)；定位：相同两个交易日和 interval=1d；close 489.20 / 494.35，窗口未返回 distribution/split/capitalGains 事件。
- **AAPL**：[ Apple reports first quarter results ](https://www.apple.com/newsroom/2024/02/apple-reports-first-quarter-results/)；定位：股息段：现金股息 0.24，record date 2024-02-12，payable 2024-02-15；公告日即 2 月 1 日不表示当天除息。
- **AMZN**：[ Yahoo Finance Chart historical daily dataset: AMZN ](https://query1.finance.yahoo.com/v8/finance/chart/AMZN?period1=1706745600&period2=1707091200&interval=1d&events=div%2Csplits%2CcapitalGains)；定位：chart.result[0]：timestamp 按 exchangeTimezoneName=America/New_York 转为 2024-02-01、2024-02-02；indicators.quote[0].close 与 indicators.adjclose[0].adjclose 对应两个交易日；events=div,splits,capitalGains 的请求未返回窗口事件。
- **AMZN**：[ Yahoo Finance Chart historical daily dataset: SPY ](https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1=1706745600&period2=1707091200&interval=1d&events=div%2Csplits%2CcapitalGains)；定位：相同两个交易日和 interval=1d；close 489.20 / 494.35，窗口未返回 distribution/split/capitalGains 事件。
- **META**：[ Yahoo Finance Chart historical daily dataset: META ](https://query1.finance.yahoo.com/v8/finance/chart/META?period1=1706745600&period2=1707091200&interval=1d&events=div%2Csplits%2CcapitalGains)；定位：chart.result[0]：timestamp 按 exchangeTimezoneName=America/New_York 转为 2024-02-01、2024-02-02；indicators.quote[0].close 与 indicators.adjclose[0].adjclose 对应两个交易日；events=div,splits,capitalGains 的请求未返回窗口事件。
- **META**：[ Yahoo Finance Chart historical daily dataset: SPY ](https://query1.finance.yahoo.com/v8/finance/chart/SPY?period1=1706745600&period2=1707091200&interval=1d&events=div%2Csplits%2CcapitalGains)；定位：相同两个交易日和 interval=1d；close 489.20 / 494.35，窗口未返回 distribution/split/capitalGains 事件。
- **META**：[ Meta Reports Fourth Quarter and Full Year 2023 Results; Initiates Quarterly Dividend ](https://investor.atmeta.com/investor-news/press-release-details/2024/Meta-Reports-Fourth-Quarter-and-Full-Year-2023-Results-Initiates-Quarterly-Dividend/default.aspx)；定位：Meta Initiates Quarterly Dividend：首次季度股息 0.50，record date 2024-02-22，payable 2024-03-26；宣告股息不表示 2 月 2 日除息。

## 第一轮证据自查

- 名单：从 5 个 task.json 提取 26 个 `(task_id, entity_id)`，与参考 JSON 完全一致；没有缺行、增行或重复键。
- 数值：15 个 EPS 与对应原始单季 XBRL 观察值一致；8 个银行增长值用十进制公式重算；AAPL consensus 分档满足严格的 ±5% 规则。
- 日期：季度起止、首次 earnings 公告、SEC filed 与 task cutoff/resolution 分开；Amgen 日期冲突已降为 provisional，AMD/TMO 的财历差异保留。
- 信用：4 个 Chapter 11 日期落在完整窗口；4 个 no_event 均检查窗口内 8-K/8-K/A/10-K/10-Q 元数据，并结合覆盖窗口后端的财报，保持 provisional。
- 行情：四个 ticker 日期、币种、两个价格点、窗口事件与 close/adjclose 标签一致性均检查；未使用 Jan31 或 S&P 指数替代 SPY。
- schema：标签均属于各 task 允许集合；target_type 与 task 一致；非空数值均有限；状态只使用允许枚举；未写 predictions 字段。
- 数据隔离：历史来源均为公开事件/财报/公开行情 vendor，未访问组织者隐藏 outcome 或榜单；这些事后文件只能供本地实验/开发验证。

23 个完整原始结构化响应（15 个 SEC EPS 单指标、4 个 SEC 申报目录、4 个 Yahoo 行情）的本地 SHA-256 回读均通过；14 个同比 baseline 也与原始 prior 观察值一致，Apple exemplar 的 1.50 仅来自题面 consensus。4 个 SEC 申报目录的 recent 最早日期都早于窗口起点，archive ranges 均早于窗口，因此目录范围完整；这项完整性检查不等于穷尽事件证明。

机器可读自查证据：`sources/earnings-credit/evidence-self-check.json`。请求/申报元数据及文件 SHA-256 将索引于 `sources/earnings-credit/evidence-index.json`。行情 raw 文件允许重新检查响应哈希；SEC Company Facts 只存最小相关观察值和下载时原始 SHA-256；另存 15 个完整 companyconcept 单 EPS 指标结构化 raw，可直接验证哈希及 actual/prior 观察值。未保存完整 companyfacts 或大篇公司公告全文。

Nasdaq historical API 曾返回 HTTP 200 但 `totalRecords=0`；已留存其响应与哈希，未把空响应当作价格缺失事件或零收益。Yahoo 网页浏览曾返回 429，公开 Chart 数据端点由标准库请求成功。

## 0.1.1补证接力

新增信用原始正文见[补证报告](../sources/credit-supplement/report.md)，AMGN预告/实际公告见[日期补证](../sources/amgn-supplement/README.md)，行情展示与公司行动见[股价补证](../sources/postearn-supplement/00-补证报告.md)。核心结果、标签与状态未变；合并JSONL的source/notes已加入这些证据。Yahoo close与adjclose是同源序列检查，不能当作独立第二行情源。

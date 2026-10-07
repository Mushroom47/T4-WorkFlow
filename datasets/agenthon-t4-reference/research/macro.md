# CPI 与宏观修订公开历史参考

检索与取回日期：2026-10-07。范围为 `t4-cpicomp-202410-us11`（11 个实体）和 `t4-macrorev-20240930-us6`（12 个实体）。23 行全部为 `verified`，`provisional` 与 `unresolved` 均为 0。`verified` 表示公开历史来源与本地计算可复核，不代表组织者私有答案已验证。

这些文件仅用于用户授权的本地历史参考、实验与验证。结果发布日期在题目 cutoff 之后，不能放入受 frozen-corpus/embargo 约束的预测证据。未获取私有 outcome，也未通过 Development 榜单探测标签。

## CPI 首次发布与精度

CPI 统一锁定 2024-11-13 vintage 的 2024-09 与 2024-10 季调指数，公式为 `100 × (October index / September index − 1)`。JSON 的 `reference_value` 保留从已发表三位小数指数推算的浮点数，`inputs` 同时登记 BLS 发布稿的一位小数环比。不能把指数推算值称为 BLS 内部未舍入环比。原 task 的 corpus 用两位小数环比，card provenance 指向 ALFRED 2024-11-13 outcome vintage；组织者的确切舍入规则未公开。

[BLS 2024-11-13 October CPI 历史发布稿](https://www.bls.gov/news.release/archives/cpi_11132024.htm) 是日期、季调口径及一位小数显示值的主要核对来源。发布稿技术说明指出季调因子会在年度重算时修订前五年指数，因此使用今日 FRED/BLS 序列会改变本任务的历史结果。

| entity_id | September 首次 vintage 指数 | October 首次 vintage 指数 | 推算 MoM (%) | BLS 显示 (%) |
| --- | ---: | ---: | ---: | ---: |
| CPI_ALLITEMS | 314.686 | 315.454 | +0.24405280 | +0.2 |
| CPI_APPAREL | 133.350 | 131.407 | -1.45706787 | -1.5 |
| CPI_CORE | 320.767 | 321.666 | +0.28026574 | +0.3 |
| CPI_ENERGY | 271.703 | 271.646 | -0.02097879 | +0.0 |
| CPI_FOOD | 331.752 | 332.278 | +0.15855217 | +0.2 |
| CPI_GASOLINE | 281.279 | 278.824 | -0.87279889 | -0.9 |
| CPI_MEDICAL | 565.984 | 567.587 | +0.28322355 | +0.3 |
| CPI_NEWVEH | 177.051 | 176.966 | -0.04800877 | +0.0 |
| CPI_SHELTER | 404.045 | 405.590 | +0.38238315 | +0.4 |
| CPI_TRANSPSVC | 439.364 | 441.301 | +0.44086452 | +0.4 |
| CPI_USEDCARS | 173.566 | 178.290 | +2.72173121 | +2.7 |

每个系列的公开 CSV URL、表头、两个指数输入与原件 SHA256 都登记在 JSON。CSV 表头使用 `<series>_20241113`，不是今日 vintage。

## 宏观修订逐行比较

每个实体按自己的 `resolving_release_date` 取 vintage、读取 `ref_month` 水平，并与 task 给定的 `latest_precutoff_estimate` 比较。全部 12 个 pre-cutoff baseline 均与对应 ALFRED vintage 的公开 CSV 完全一致。比较对象是同月水平，不是最近一次环比变化。

| entity_id | cutoff 前水平 | 指定发布日水平 | 差额 | label | 单位 |
| --- | ---: | ---: | ---: | --- | --- |
| DGORDER_2024-07_20241025 | 289587 | 289419 | -168 | down | millions of dollars, SA |
| DGORDER_2024-08_20241025 | 289720 | 287018 | -2702 | down | millions of dollars, SA |
| HOUST_2024-07_20241018 | 1237 | 1262 | +25 | up | thousands of units, SAAR |
| INDPRO_2024-07_20241017 | 102.306 | 102.586 | +0.2805 | up | index 2017=100, SA |
| INDPRO_2024-08_20241017 | 103.139 | 102.933 | -0.206 | down | index 2017=100, SA |
| PAYEMS_2024-07_20241004 | 158637 | 158692 | +55 | up | thousands of persons, SA |
| PAYEMS_2024-08_20241004 | 158779 | 158851 | +72 | up | thousands of persons, SA |
| PAYEMS_2024-08_20241101 | 158779 | 158770 | -9 | down | thousands of persons, SA |
| PI_2024-07_20241031 | 24803.2 | 24819.3 | +16.1 | up | billions of dollars, SAAR |
| PI_2024-08_20241127 | 24853.7 | 24740.2 | -113.5 | down | billions of dollars, SAAR |
| RSAFS_2024-07_20241017 | 710409 | 710851 | +442 | up | millions of dollars, SA |
| RSAFS_2024-08_20241115 | 710773 | 710038 | -735 | down | millions of dollars, SA |

`PAYEMS_2024-08_20241004` 为 `up`，而 `PAYEMS_2024-08_20241101` 为 `down`：同月不同 resolving vintage 保留为独立实体。另一个容易混淆的例子是 `PI_2024-08_20241127`，参考值取 11 月 27 日表格的 August 水平，不能用 10 月 31 日的较早更新替代。

## 官方来源交叉核对

- [BLS 2024-10-04 Employment Situation](https://www.bls.gov/news.release/archives/empsit_10042024.htm) 与 [2024-11-01 发布稿](https://www.bls.gov/news.release/archives/empsit_11012024.htm)：Table B-1 的 Total nonfarm 季调水平，千人整数。
- [Census 2024-10-25 Durable Goods](https://www.census.gov/manufacturing/m3/historical_data/pressreleases/adv/2024/sep24adv.pdf)：PDF 第 6 页 Table 1 的 Total New Orders，季调百万美元整数。
- [Census / HUD 2024-10-18 New Residential Construction](https://www.census.gov/construction/nrc/pdf/newresconst_202409.pdf)：PDF 第 5 页 Table 3a 的 July United States Total，千套 SAAR 整数。
- [Federal Reserve 2024-10-17 G.17](https://www.federalreserve.gov/releases/g17/20241017/default.htm)：Total index 的 July / August 当期与前次值仅一位小数；ALFRED 同日 vintage 保存四位小数。
- [BEA 2024-10-31 当期 XLSX](https://www.bea.gov/sites/default/files/2024-10/pi0924.xlsx) 与 [2024-11-27 当期 XLSX](https://www.bea.gov/sites/default/files/2024-11/pi1024.xlsx)：Table 1 Line 1，十亿美元 SAAR 一位小数；分别读取 July 和 August 列。原始 ZIP/XML 用 Python stdlib 读取，没有安装依赖。
- [Census 2024-10-17 Retail Sales](https://www2.census.gov/retail/releases/historical/marts/adv2409.pdf) 与 [2024-11-15 发布表](https://www2.census.gov/retail/releases/historical/marts/adv2410.pdf)：PDF 第 5 页 Table 1 的 Retail & food services, total，Adjusted 的相应月份，百万美元整数。

## 可复核性与访问限制

ALFRED 公开 `alfredgraph.csv` 接口不需要 API key。本次所有显式 vintage 取回均成功，响应列名中的日期、observation_date 及值已核对；[ALFRED 官方下载说明](https://alfred.stlouisfed.org/help/downloaddata) 定义 vintage 为历史时点实际可获得的数据。接口示例：

```text
https://alfred.stlouisfed.org/graph/alfredgraph.csv?id=INDPRO&cosd=2024-07-01&coed=2024-08-01&vintage_date=2024-10-17
```

证据目录为 `datasets/agenthon-t4-reference/sources/macro/`。`alfred-downloads.json` 保存每次 CSV 的查询参数、URL、取回日期、解析行与 SHA256；`release-downloads.json` 保存官方原件的 URL/hash 或具体下载错误；`release-evidence.json` 保存必要的表格值与定位。所有下载的 CSV hash 已回读核对。

BLS 原始 HTML 的 stdlib 下载返回 `HTTP Error 403: Forbidden`，但官方 archive 已由 web 浏览读取，且数值由公开 ALFRED CSV 独立支持。BEA October 31 XLSX 首次并行下载出现 TLS EOF，单独重试成功并与对应 ALFRED 水平一致。不存在未解决的实体数值缺口。

后续本地验证时应直接使用 JSON 中的公式及 inputs 回算；若实验实现选择两位小数或 BLS 一位小数口径，须明确记录该精度选择，不能将其默认为组织者私有评分口径。

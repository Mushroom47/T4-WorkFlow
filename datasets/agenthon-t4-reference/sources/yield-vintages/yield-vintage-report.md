# FOMC 国债收益率的历史 vintage 补证

已完成两个公开任务、12实体和24个起止端点的历史版本对照。每个端点实际查询观察日前一日、当日、次日三个 ALFRED vintage，共72份原始CSV；全部下载成功、列名及回读SHA一致。24个目标观察值都在前一日/当日 vintage 中缺失，在次日 vintage 中出现。历史值与任务起值、现有财政部XML均一致，12个基点变化与既有参考值差异全部为0。

这补足了当前历史XML之外的明确历史as-of版本证据。它证明在这些过去日期ALFRED可见的数字，尚未证明四个观察日Treasury源网页的全球首次发布时间或精确盘中更新时间。`global_source_first_publication_proven=false` 保持明确。

## 窗口与逐行结果

起止窗口完全来自冻结 task：2022-07-28 → 2022-09-20，以及2024-09-19 → 2024-11-06。单位均为 `bps_change`；计算式为 `(历史终点收益率百分数 − task.start_yield_pct) × 100`。起点历史值同时对照冻结task与财政部XML，防止使用错误交易日或换成整段期间收益。

| task_id | entity_id / series | 起点(%) | 起点最早测试可见vintage | 终点(%) | 终点最早测试可见vintage | 重算(bps) | 与既有参考差异(bps) |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: |
| t4-fomc-curve-20220728 | UST2Y / DGS2 | 2.85 | 2022-07-29 | 3.96 | 2022-09-21 | 111 | 0 |
| t4-fomc-curve-20220728 | UST3Y / DGS3 | 2.81 | 2022-07-29 | 3.94 | 2022-09-21 | 113 | 0 |
| t4-fomc-curve-20220728 | UST5Y / DGS5 | 2.69 | 2022-07-29 | 3.75 | 2022-09-21 | 106 | 0 |
| t4-fomc-curve-20220728 | UST7Y / DGS7 | 2.69 | 2022-07-29 | 3.69 | 2022-09-21 | 100 | 0 |
| t4-fomc-curve-20220728 | UST10Y / DGS10 | 2.68 | 2022-07-29 | 3.57 | 2022-09-21 | 89 | 0 |
| t4-fomc-curve-20220728 | UST30Y / DGS30 | 3.02 | 2022-07-29 | 3.59 | 2022-09-21 | 57 | 0 |
| t4-fomc-curve-20240918 | UST2Y / DGS2 | 3.59 | 2024-09-20 | 4.27 | 2024-11-07 | 68 | 0 |
| t4-fomc-curve-20240918 | UST3Y / DGS3 | 3.47 | 2024-09-20 | 4.20 | 2024-11-07 | 73 | 0 |
| t4-fomc-curve-20240918 | UST5Y / DGS5 | 3.49 | 2024-09-20 | 4.27 | 2024-11-07 | 78 | 0 |
| t4-fomc-curve-20240918 | UST7Y / DGS7 | 3.60 | 2024-09-20 | 4.37 | 2024-11-07 | 77 | 0 |
| t4-fomc-curve-20240918 | UST10Y / DGS10 | 3.73 | 2024-09-20 | 4.42 | 2024-11-07 | 69 | 0 |
| t4-fomc-curve-20240918 | UST30Y / DGS30 | 4.06 | 2024-09-20 | 4.60 | 2024-11-07 | 54 | 0 |

## 证据与日期边界

[ALFRED Download Data Help](https://alfred.stlouisfed.org/help/downloaddata)解释vintage用于重建过去日期可见的数据。这里逐CSV验证带日期的列名，并实际筛选 `observation_date`；不是凭URL的vintage参数或文件名认定目标日在该版本存在。没有用当前FRED值替换历史版本。

[ALFRED Help](https://alfred.stlouisfed.org/help)说明新值/修订通常在发布后一个工作日内加入；release日期优先来自原始源，否则可来自provider或FRED首次可用日。因此观察日、ALFRED最早测试可见日期、源发布日期和本次retrieval日期分别保存。这里的次日vintage转换不被硬称为Treasury全球首发。

[Fed H.15当前页面](https://www.federalreserve.gov/releases/h15/default.htm)说明当前周一至周五4:15pm发布，假日或Board关闭不发布；[About页](https://www.federalreserve.gov/releases/h15/about.htm)说明每个非假日工作日发布。目标日H.15历史目录尝试未取得原稿。当前规则只能作发布机制背景，本次不能给2022/2024各观察值补造精确首次发布时间。

ALFRED官方还提供Initial Release Only格式，含 `realtime_start_date`；本次已取得明确历史vintage CSV，未取得该格式导出或带实时区间的原始API字段。这是进一步收紧原始发布时间证明的可公开后续路径。

起点观察日是task已经给定的cutoff-close数字；ALFRED同日vintage尚未收录该日值，不应被解释为题面没有提供baseline。12个task给定起值均与次日最早测试可见版本一致。

## 原件、摘要与复现

- `*_window-*_vintage-*.csv`：72份原始HTTP CSV字节，配套`.metadata.json`保存URL、UTC retrieval时间、SHA-256、返回范围及目标日期存在性。
- `DGS10_obs-2022-09-20_vintage-*.csv`：3份最初探测原件；其中在尚无目标观察时ALFRED回退返回较长历史，原字节保留。主对照使用包含过去7天的范围，避免把回退响应误认成目标日数据。
- `downloads.json`：72份主请求的下载登记。
- `vintage-comparison.json`：12行离线计算摘要、24端点逐日存在性与差值检查，不是源原始响应。
- `primary-context-evidence.json`：官方说明的浏览摘录及定位，明确不是HTTP原始字节。当前说明HTML另尝试下载；失败状态和错误按实际写入元数据。
- `evidence-manifest.json`：供root统一离线哈希审校的清单；原始来源与派生摘要用status区分，published_at无法证明时为null。

本次只写 `sources/yield-vintages/`，没有修改共享reference/research/qa/manifest/docs。未调用私有outcome或外发任何消息。

```bash
python3 datasets/agenthon-t4-reference/sources/yield-vintages/collect_yield_vintages.py download
python3 datasets/agenthon-t4-reference/sources/yield-vintages/collect_yield_vintages.py audit
```

标准库执行环境、脚本SHA与原task/XML的SHA保存在计算摘要。yield CSV原值保留两位小数；基点用Decimal计算，避免浮点尾差。当前版本与早期vintage的零差异是本次24端点的实际结果，不推断其他日期从未修订。

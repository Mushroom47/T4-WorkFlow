# 信用事件参考集的原始正文补充与检索边界

本补充仅为本地事后参考证据归档。四个正例现在各有原始 SEC 8-K 正文可离线核验；四个负例有全观察窗相关申报主文件与窗口后季度正文。**不修改参考标签状态，不把未检出事件升级为已证明无事件。主办方 #26 未回复，正式评分仍缺。**

本次分母是 **80 份 SEC 原始正文 + 8 份原始 SEC submissions JSON = 88 个下载来源**，全部本地 bytes/SHA-256 回读通过；正文合计 54,998,591 bytes（约 55 MB）。这不是 80/88 条实体记录，更不是数值复算数量。信用任务仍只有 8 个实体，其数值字段留空。

- 四正例：4 份原始 8-K；另有 BBBY 公告附件、RAD 更正 8-K/A，共 6 份正文。
- 四暂定负例：观察窗内 70 份 8-K/8-K/A/10-K/10-Q 主文件，加窗口后首个 10-Q 各 1 份，共 74 份正文。
- 原始 bytes 位于 `documents/<ticker>/` 与 `<ticker>-submissions.raw.json`。派生筛选定位位于 `body-checks.json`，人工候选上下文记录位于 `candidate-context-review.json`；这两个摘要不计入原始正文数量。

来源清单为 [evidence-manifest.json](evidence-manifest.json)，包含每个原始文件相对此目录的 `path`、`url`、`sha256`、`bytes`、`retrieved_at`、`status`、`locator`、`published_at`。本次所有 88 个来源均 `downloaded`，没有未保存正文仍计入独立审校的条目。

## 四正例：直接回读原文的定位

观察窗为 **(2023-03-31, 2024-03-31]**。下面各文件的 Item 1.03 申请段直接包含 issuer、申请 Chapter 11、申请日期及法院辖区，满足事件定义的一项即可确证正标签。正文公司与 ticker/CIK 的映射也已检查。

| entity / CIK | 事件日 | SEC 公开申报日 | 原始主 8-K 相对路径 | 正文定位（去 HTML、反转义、合并空白后） |
|---|---|---|---|---|
| BBBY / 0000886158 | 2023-04-23 | 2023-04-24 | [documents/BBBY/2023-04-24-0001193125-23-111754-d465247d8k.htm](https://www.sec.gov/Archives/edgar/data/886158/000119312523111754/d465247d8k.htm) | `Item 1.03`；`On\s+April\s+23,\s+2023`；同段查 `filed.*voluntary\s+petition`、`Chapter\s+11`、`District of New Jersey`；派生正文 offset 2232 |
| RAD / 0000084129 | 2023-10-15 | 2023-10-16 | [documents/RAD/2023-10-16-0001104659-23-109236-tm2328505d1_8k.htm](https://www.sec.gov/Archives/edgar/data/84129/000110465923109236/tm2328505d1_8k.htm) | `Item 1.03`；`On\s+October\s+15,\s+2023`；同段查 `filed.*voluntary\s+petition`、`Chapter\s+11`、`District of New Jersey`；派生正文 offset 2430 |
| WE / 0001813756 | 2023-11-06 | 2023-11-07 | [documents/WE/2023-11-07-0001193125-23-271902-d522028d8k.htm](https://www.sec.gov/Archives/edgar/data/1813756/000119312523271902/d522028d8k.htm) | `Item 1.03`；`On\s+November\s+6,\s+2023`；同段查 `filed.*voluntary\s+petition`、`Chapter\s+11`、`District of New Jersey`；派生正文 offset 2775 |
| YELL / 0000716006 | 2023-08-06 | 2023-08-07 | [documents/YELL/2023-08-07-0001193125-23-204370-d483482d8k.htm](https://www.sec.gov/Archives/edgar/data/716006/000119312523204370/d483482d8k.htm) | `Item 1.03`；`On\s+August\s+6,\s+2023`；同段查 `filed.*voluntary\s+petition`、`Chapter\s+11`、`District of Delaware`；派生正文 offset 2063 |

日期 regex 允许原文的换行/不间断空白，但必须先去除标签并做 HTML 实体反转义。不能直接在原始 HTML 上要求整段英文连续出现。offset 是 `body-checks.json` 所定义的派生 visible-text 字符位置，不是 raw bytes 位置；独立审校应直接从本地 `.htm` 构建正文后核查。

- **BBBY**：[SEC 原始主文件](https://www.sec.gov/Archives/edgar/data/886158/000119312523111754/d465247d8k.htm)；本地 SHA-256 `8edd4844eef01c0408a5c52ec0fd613fd1ffa0ebecc79e7e8dd10ef73a90be98`，获取 `2026-10-07T08:46:21.518500+00:00`。
- **RAD**：[SEC 原始主文件](https://www.sec.gov/Archives/edgar/data/84129/000110465923109236/tm2328505d1_8k.htm)；本地 SHA-256 `dd268a32e6e889a522776a564a924aea28a04fb6e2c2b12b78752af4143f94b0`，获取 `2026-10-07T08:46:22.899043+00:00`。
- **WE**：[SEC 原始主文件](https://www.sec.gov/Archives/edgar/data/1813756/000119312523271902/d522028d8k.htm)；本地 SHA-256 `3e12e2ef58276847376a12294e44bfbb4695f506b466b388bcfb0433b8323dce`，获取 `2026-10-07T08:46:23.482194+00:00`。
- **YELL**：[SEC 原始主文件](https://www.sec.gov/Archives/edgar/data/716006/000119312523204370/d483482d8k.htm)；本地 SHA-256 `ba3bcd37b07b8653d4d6570daf63d1901bdd6b4ab2b92c3e244f3f691f455885`，获取 `2026-10-07T08:46:24.410222+00:00`。

BBBY 的 [公告附件](https://www.sec.gov/Archives/edgar/data/886158/000119312523111754/d465247dex991.htm) 正文署期为 **2023-04-23**，但此 SEC URL 纳入公开申报的日期为 **2023-04-24**；manifest 的 `published_at` 使用 SEC filingDate，公告署期另记 `document_date`。RAD 的 [更正 8-K/A](https://www.sec.gov/Archives/edgar/data/84129/000110465923109413/tm2328535d1_8ka.htm) 明确更正附件 Exhibit 10.1，其他披露保持相同；本次同时保存原始 8-K，避免只依赖更正文件。

以上原文直接覆盖 Chapter 11 条件、窗口日期和历史 issuer/ticker；不宣称所有全球子公司均申请破产，也不需要借助违约概率或 distressed-exchange 推断。

## 四暂定负例：完整分母与窗口尾部

| entity | 窗内 10-Q | 窗内 10-K | 窗内 8-K | 窗内 8-K/A | 窗内主文件总数 | 补充季度 period end | 含尾部正文总数 |
|---|---:|---:|---:|---:|---:|---|---:|
| BBY | 3 | 1 | 9 | 2 | 15 | 2024-05-04 | 16 |
| M | 3 | 1 | 10 | 0 | 14 | 2024-05-04 | 15 |
| ODFL | 3 | 1 | 15 | 2 | 21 | 2024-03-31 | 22 |
| WBA | 3 | 1 | 14 | 2 | 20 | 2024-05-31 | 21 |

SEC 目录 recent 的最早申报日期早于窗口起点，archive files 的日期范围均在窗口之前，因此本次 70 份分母能够从原始 submissions JSON 重新生成；名单不是搜索引擎返回的片段集合。四个目录均没有窗内 Item 1.03 或 2.04。此事实只证明所检查目录中没有这两类条目，不能证明无其他披露方式或未披露事件。

年度和季度覆盖关系：BBY/M 年度结束于 2024-02-03，其窗口后季度结束于 2024-05-04，覆盖 2 月 4 日至 3 月 31 日尾部；ODFL 年度结束于 2023-12-31，下一季恰于 2024-03-31 结束；WBA 年度结束于 2023-08-31，窗内季度至 2024-02-29，下一季度至 2024-05-31，覆盖 3 月尾部。ODFL 窗内第一份 10-Q 的报告期截至 2023-03-31，其公开申报日虽在窗内，但该期末本身只到观察窗起点，后续季度与年度材料提供后面的覆盖。

## 债务、评级与候选词的正文复核

下列定位可在本地正文查找。它们为 provisional 提供可复核的证据链，不是覆盖所有三类信用事件的充分证明。

- **BBY**：年度 MD&A / Sources of Liquidity 与 Note 8 Debt：2024-02-03 全财务 covenants 合规；截至 2024-03-13 评级保持 S&P BBB+/Stable、Moody’s A3/Stable。尾部季度 Note 6 Debt：2024-05-04、2024-02-03、2023-04-29 循环授信无借款；2028/2030 notes 本金继续列示 500/650 百万美元。 [年度原文](https://www.sec.gov/Archives/edgar/data/764478/000076447824000010/bby-20240203x10k.htm)；[覆盖尾部的季度原文](https://www.sec.gov/Archives/edgar/data/764478/000076447824000022/bby-20240504x10q.htm)。
- **M**：年度 Note 6 Financing Activities：FY2023 除 ABL 外没有其他重大债务融资活动；年度 MD&A 评级表截至 2024-02-03 为 Moody’s Ba1、S&P BB+、Fitch BBB-，三者 Stable；现金流补充表实际利息支付 157 百万美元。尾部季度 Note 4：13周内除资本租赁外无借入/偿还债务，2024-02-03 与 2024-05-04 unsecured notes/debentures 本金同为 3,007 百万美元。 [年度原文](https://www.sec.gov/Archives/edgar/data/794367/000162828024012734/m-20240203.htm)；[覆盖尾部的季度原文](https://www.sec.gov/Archives/edgar/data/794367/000162828024025853/m-20240504.htm)。
- **ODFL**：年度及尾部季度 MD&A / General Debt Provisions：截至 2023-12-31、2024-03-31 的期间所有 outstanding debt instruments covenants 合规；2023-05-04 偿还 20 百万美元本金，余 80 百万美元；年度现金流补充表实付利息 3.484 百万美元。 [年度原文](https://www.sec.gov/Archives/edgar/data/878927/000095017024020176/odfl-20231231.htm)；[覆盖尾部的季度原文](https://www.sec.gov/Archives/edgar/data/878927/000095017024054284/odfl-20240331.htm)。
- **WBA**：年度 Note 8 Debt 和季度 Note 7 Debt / Debt covenants：截至 2023-08-31、2024-02-29、2024-05-31 applicable financial covenants 合规；截至 2024-02-29 的六个月实付利息约 301 百万美元，九个月至 2024-05-31 约 460 百万美元。October/December 2023 评级降至 S&P BBB-/Negative、Moody’s Ba2/Stable；下调本身不等于题面信用事件。 [年度原文](https://www.sec.gov/Archives/edgar/data/1618921/000161892123000062/wba-20230831.htm)；[覆盖尾部的季度原文](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000065/wba-20240531.htm)。

全文词筛查发现的明显候选已读上下文：BBY 的 failure-to-pay 文字属于授信协议默认触发条款；M 的 receivership 文字指其他银行未来的假设，missed-payment 文字指消费者信用卡逾期收费；WBA 的 bankruptcy/payment-defaults 文字属于新增授信协议的事件条款。没有把这些假设或他方事件错误当成 issuer 实际事件。具体相对路径和定位见 [candidate-context-review.json](candidate-context-review.json)。

所有 74 份负例正文都筛查 `Chapter 11/7`、bankruptcy/receivership、付款失败、distressed exchange、generic default、covenant compliance、interest paid、financing/ratings 关键词。筛查范围与 exact regex 在 `body-checks.json`；结果只用于检索定位，零命中不证明无事件，命中也不自动判定事件。

## 尚未覆盖的检索边界与集成建议

- 全部原文是当前获取的 SEC Archive 响应。SEC filingDate 与公告正文署期可复核，但未获得首发时 bytes hash；不能将当前文件 hash 称为首发版本 hash。
- no_event 的全窗口 SEC 主文件原文/目录完整性不等于穷尽三类事件。法院案卷、全部评级机构的历史违约/选择性违约/distressed exchange 记录未完成穷尽检索，4条仍 provisional。
- 70份窗口申报仅涵盖 8-K/8-K/A/10-K/10-Q primaryDocument；exhibits、其他表单和可能未披露/非重大债务事件未穷尽。
- 检索主体按任务历史 CIK/issuer 识别；没有把后续同名公司、现 ticker 或全部全球子公司任意并入。各子公司事件是否映射到任务 issuer 仍需按公开定义单独核对。
- 正文关键词命中、财务 covenant 合规、正常评级或偿债累计值各自都不能单独证明 no_event；关键词零命中也不能证明无事件。
- 本补充只用于事后本地参考，未更改 reference/research/qa/manifest 共享文件；主办方#26未回复，正式评分缺口仍在。

建议集成时将本目录作为补充证据源：只把 manifest 中 `status=downloaded` 且本地 hash/bytes 匹配的来源计入离线审校；先对四个正例从原始主 8-K 直接核查日期、issuer、ticker和申请 Chapter 11 的同段文本，再检查四个负例名单分母与尾部正文。保留四条 no_event 的 provisional 和“未穷尽法院/评级台账”标识，避免在报告中把目录完整性、正文哈希通过或正常 covenant 信息称为完整无事件证明。

若未来要升级 no_event，需要针对各 issuer 与任务认可的子公司范围，补充完整法院案卷检索，以及 S&P/Moody’s/Fitch 等评级机构在该窗口的历史 default / selective default / distressed exchange 台账，并保存真实可访问的原始资料和搜索范围；若服务要求认证或只有当前评级，不得推断历史完整性。本次未使用付费凭据或隐藏答案。

## 74 份负例正文名单

| entity | role | form | filingDate | reportDate | Items | 原始正文相对路径 |
|---|---|---|---|---|---|---|
| BBY | 窗内 | 8-K | 2023-04-13 | 2023-04-12 | 1.01,1.02,9.01 | [documents/BBY/2023-04-13-0000764478-23-000012-bby-20230412x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000012/bby-20230412x8k.htm) |
| BBY | 窗内 | 8-K | 2023-04-27 | 2023-04-24 | 5.02 | [documents/BBY/2023-04-27-0000764478-23-000016-bby-20230424x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000016/bby-20230424x8k.htm) |
| BBY | 窗内 | 8-K | 2023-05-25 | 2023-05-25 | 2.02,9.01 | [documents/BBY/2023-05-25-0000764478-23-000019-bby-20230525x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000019/bby-20230525x8k.htm) |
| BBY | 窗内 | 10-Q | 2023-06-02 | 2023-04-29 | — | [documents/BBY/2023-06-02-0000764478-23-000025-bby-20230429x10q.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000025/bby-20230429x10q.htm) |
| BBY | 窗内 | 8-K | 2023-06-16 | 2023-06-14 | 5.07 | [documents/BBY/2023-06-16-0000764478-23-000027-bby-20230614x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000027/bby-20230614x8k.htm) |
| BBY | 窗内 | 8-K | 2023-08-01 | 2023-07-28 | 5.02 | [documents/BBY/2023-08-01-0000764478-23-000035-bby-20230728x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000035/bby-20230728x8k.htm) |
| BBY | 窗内 | 8-K | 2023-08-29 | 2023-08-29 | 2.02,9.01 | [documents/BBY/2023-08-29-0000764478-23-000038-bby-20230829x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000038/bby-20230829x8k.htm) |
| BBY | 窗内 | 10-Q | 2023-09-01 | 2023-07-29 | — | [documents/BBY/2023-09-01-0000764478-23-000041-bby-20230729x10q.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000041/bby-20230729x10q.htm) |
| BBY | 窗内 | 8-K/A | 2023-09-12 | 2023-07-28 | 5.02 | [documents/BBY/2023-09-12-0000764478-23-000046-bby-20230728x8ka.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000046/bby-20230728x8ka.htm) |
| BBY | 窗内 | 8-K | 2023-11-21 | 2023-11-21 | 2.02,9.01 | [documents/BBY/2023-11-21-0000764478-23-000049-bby-20231121x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000049/bby-20231121x8k.htm) |
| BBY | 窗内 | 10-Q | 2023-12-01 | 2023-10-28 | — | [documents/BBY/2023-12-01-0000764478-23-000053-bby-20231028x10q.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000053/bby-20231028x10q.htm) |
| BBY | 窗内 | 8-K/A | 2023-12-13 | 2023-03-28 | 5.02 | [documents/BBY/2023-12-13-0000764478-23-000056-bby-20230328x8ka.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447823000056/bby-20230328x8ka.htm) |
| BBY | 窗内 | 8-K | 2024-02-29 | 2024-02-29 | 2.02,9.01 | [documents/BBY/2024-02-29-0000764478-24-000003-bby-20240229x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447824000003/bby-20240229x8k.htm) |
| BBY | 窗内 | 8-K | 2024-03-07 | 2024-03-05 | 5.02 | [documents/BBY/2024-03-07-0000764478-24-000006-bby-20240305x8k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447824000006/bby-20240305x8k.htm) |
| BBY | 窗内 | 10-K | 2024-03-15 | 2024-02-03 | — | [documents/BBY/2024-03-15-0000764478-24-000010-bby-20240203x10k.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447824000010/bby-20240203x10k.htm) |
| BBY | 尾部季度 | 10-Q | 2024-06-07 | 2024-05-04 | — | [documents/BBY/2024-06-07-0000764478-24-000022-bby-20240504x10q.htm](https://www.sec.gov/Archives/edgar/data/764478/000076447824000022/bby-20240504x10q.htm) |
| M | 窗内 | 8-K | 2023-05-23 | 2023-05-19 | 5.07 | [documents/M/2023-05-23-0000794367-23-000055-n-20230519.htm](https://www.sec.gov/Archives/edgar/data/794367/000079436723000055/n-20230519.htm) |
| M | 窗内 | 8-K | 2023-05-26 | 2023-05-25 | 5.02 | [documents/M/2023-05-26-0000794367-23-000061-n-20230525.htm](https://www.sec.gov/Archives/edgar/data/794367/000079436723000061/n-20230525.htm) |
| M | 窗内 | 8-K | 2023-06-01 | 2023-06-01 | 2.02,9.01 | [documents/M/2023-06-01-0001628280-23-020415-n-20230601.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828023020415/n-20230601.htm) |
| M | 窗内 | 10-Q | 2023-06-06 | 2023-04-29 | — | [documents/M/2023-06-06-0001628280-23-021104-m-20230429.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828023021104/m-20230429.htm) |
| M | 窗内 | 8-K | 2023-08-22 | 2023-08-22 | 2.02,9.01 | [documents/M/2023-08-22-0001628280-23-030169-n-20230822.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828023030169/n-20230822.htm) |
| M | 窗内 | 10-Q | 2023-08-25 | 2023-07-29 | — | [documents/M/2023-08-25-0001628280-23-030657-m-20230729.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828023030657/m-20230729.htm) |
| M | 窗内 | 8-K | 2023-10-31 | 2023-10-31 | 5.02 | [documents/M/2023-10-31-0000794367-23-000084-n-20231031.htm](https://www.sec.gov/Archives/edgar/data/794367/000079436723000084/n-20231031.htm) |
| M | 窗内 | 8-K | 2023-11-16 | 2023-11-16 | 2.02,9.01 | [documents/M/2023-11-16-0001628280-23-039210-n-20231116.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828023039210/n-20231116.htm) |
| M | 窗内 | 10-Q | 2023-11-28 | 2023-10-28 | — | [documents/M/2023-11-28-0001628280-23-040057-m-20231028.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828023040057/m-20231028.htm) |
| M | 窗内 | 8-K | 2024-01-22 | 2024-01-21 | 7.01,9.01 | [documents/M/2024-01-22-0000794367-24-000007-n-20240121.htm](https://www.sec.gov/Archives/edgar/data/794367/000079436724000007/n-20240121.htm) |
| M | 窗内 | 8-K | 2024-02-02 | 2024-02-02 | 5.02,7.01,9.01 | [documents/M/2024-02-02-0000794367-24-000010-n-20240202.htm](https://www.sec.gov/Archives/edgar/data/794367/000079436724000010/n-20240202.htm) |
| M | 窗内 | 8-K | 2024-02-27 | 2024-02-27 | 2.02,2.05,2.06,7.01 | [documents/M/2024-02-27-0001628280-24-007023-m-20240227.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828024007023/m-20240227.htm) |
| M | 窗内 | 8-K | 2024-03-01 | 2024-02-29 | 8.01 | [documents/M/2024-03-01-0000794367-24-000013-n-20240229.htm](https://www.sec.gov/Archives/edgar/data/794367/000079436724000013/n-20240229.htm) |
| M | 窗内 | 10-K | 2024-03-22 | 2024-02-03 | — | [documents/M/2024-03-22-0001628280-24-012734-m-20240203.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828024012734/m-20240203.htm) |
| M | 尾部季度 | 10-Q | 2024-05-30 | 2024-05-04 | — | [documents/M/2024-05-30-0001628280-24-025853-m-20240504.htm](https://www.sec.gov/Archives/edgar/data/794367/000162828024025853/m-20240504.htm) |
| ODFL | 窗内 | 8-K | 2023-04-26 | 2023-04-26 | 2.02,9.01 | [documents/ODFL/2023-04-26-0000950170-23-014592-odfl-20230426.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023014592/odfl-20230426.htm) |
| ODFL | 窗内 | 10-Q | 2023-05-08 | 2023-03-31 | — | [documents/ODFL/2023-05-08-0000950170-23-018765-odfl-20230331.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023018765/odfl-20230331.htm) |
| ODFL | 窗内 | 8-K | 2023-05-18 | 2023-05-17 | 5.07,8.01,9.01 | [documents/ODFL/2023-05-18-0000950170-23-022904-odfl-20230517.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023022904/odfl-20230517.htm) |
| ODFL | 窗内 | 8-K/A | 2023-05-18 | 2023-01-25 | 5.02 | [documents/ODFL/2023-05-18-0000950170-23-022909-odfl-20230125.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023022909/odfl-20230125.htm) |
| ODFL | 窗内 | 8-K/A | 2023-05-18 | 2023-02-28 | 5.02 | [documents/ODFL/2023-05-18-0000950170-23-022911-odfl-20230228.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023022911/odfl-20230228.htm) |
| ODFL | 窗内 | 8-K | 2023-05-18 | 2023-05-17 | 5.02 | [documents/ODFL/2023-05-18-0000950170-23-022917-odfl-20230517.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023022917/odfl-20230517.htm) |
| ODFL | 窗内 | 8-K | 2023-06-05 | 2023-06-05 | 7.01,9.01 | [documents/ODFL/2023-06-05-0000950170-23-026441-odfl-20230605.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023026441/odfl-20230605.htm) |
| ODFL | 窗内 | 8-K | 2023-06-26 | 2023-06-22 | 5.02 | [documents/ODFL/2023-06-26-0000950170-23-029863-odfl-20230622.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023029863/odfl-20230622.htm) |
| ODFL | 窗内 | 8-K | 2023-07-20 | 2023-07-20 | 8.01,9.01 | [documents/ODFL/2023-07-20-0000950170-23-033690-odfl-20230720.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023033690/odfl-20230720.htm) |
| ODFL | 窗内 | 8-K | 2023-07-26 | 2023-07-26 | 2.02,9.01 | [documents/ODFL/2023-07-26-0000950170-23-034576-odfl-20230726.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023034576/odfl-20230726.htm) |
| ODFL | 窗内 | 10-Q | 2023-08-04 | 2023-06-30 | — | [documents/ODFL/2023-08-04-0000950170-23-038553-odfl-20230630.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023038553/odfl-20230630.htm) |
| ODFL | 窗内 | 8-K | 2023-09-06 | 2023-09-06 | 7.01,9.01 | [documents/ODFL/2023-09-06-0000950170-23-046789-odfl-20230906.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023046789/odfl-20230906.htm) |
| ODFL | 窗内 | 8-K | 2023-10-19 | 2023-10-19 | 8.01,9.01 | [documents/ODFL/2023-10-19-0000950170-23-054038-odfl-20231019.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023054038/odfl-20231019.htm) |
| ODFL | 窗内 | 8-K | 2023-10-25 | 2023-10-25 | 2.02,9.01 | [documents/ODFL/2023-10-25-0000950170-23-055015-odfl-20231025.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023055015/odfl-20231025.htm) |
| ODFL | 窗内 | 10-Q | 2023-11-06 | 2023-09-30 | — | [documents/ODFL/2023-11-06-0000950170-23-059408-odfl-20230930.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023059408/odfl-20230930.htm) |
| ODFL | 窗内 | 8-K | 2023-12-05 | 2023-12-05 | 7.01,9.01 | [documents/ODFL/2023-12-05-0000950170-23-068262-odfl-20231205.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017023068262/odfl-20231205.htm) |
| ODFL | 窗内 | 8-K | 2024-01-31 | 2024-01-31 | 2.02,9.01 | [documents/ODFL/2024-01-31-0000950170-24-009181-odfl-20240131.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017024009181/odfl-20240131.htm) |
| ODFL | 窗内 | 8-K | 2024-02-16 | 2024-02-16 | 8.01,9.01 | [documents/ODFL/2024-02-16-0000950170-24-016210-odfl-20240216.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017024016210/odfl-20240216.htm) |
| ODFL | 窗内 | 10-K | 2024-02-26 | 2023-12-31 | — | [documents/ODFL/2024-02-26-0000950170-24-020176-odfl-20231231.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017024020176/odfl-20231231.htm) |
| ODFL | 窗内 | 8-K | 2024-03-05 | 2024-03-05 | 7.01,9.01 | [documents/ODFL/2024-03-05-0000950170-24-025450-odfl-20240305.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017024025450/odfl-20240305.htm) |
| ODFL | 窗内 | 8-K | 2024-03-19 | 2024-03-19 | 5.02 | [documents/ODFL/2024-03-19-0000950170-24-033550-odfl-20240319.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017024033550/odfl-20240319.htm) |
| ODFL | 尾部季度 | 10-Q | 2024-05-07 | 2024-03-31 | — | [documents/ODFL/2024-05-07-0000950170-24-054284-odfl-20240331.htm](https://www.sec.gov/Archives/edgar/data/878927/000095017024054284/odfl-20240331.htm) |
| WBA | 窗内 | 8-K | 2023-05-26 | 2023-05-26 | 7.01,9.01 | [documents/WBA/2023-05-26-0001193125-23-155537-d468351d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523155537/d468351d8k.htm) |
| WBA | 窗内 | 8-K | 2023-06-27 | 2023-06-27 | 2.02,7.01,9.01 | [documents/WBA/2023-06-27-0001193125-23-175558-d504570d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523175558/d504570d8k.htm) |
| WBA | 窗内 | 10-Q | 2023-06-27 | 2023-05-31 | — | [documents/WBA/2023-06-27-0001618921-23-000043-wba-20230531.htm](https://www.sec.gov/Archives/edgar/data/1618921/000161892123000043/wba-20230531.htm) |
| WBA | 窗内 | 8-K | 2023-07-14 | 2023-07-11 | 5.02,8.01,9.01 | [documents/WBA/2023-07-14-0001193125-23-187329-d506413d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523187329/d506413d8k.htm) |
| WBA | 窗内 | 8-K | 2023-07-27 | 2023-07-21 | 5.02,7.01,9.01 | [documents/WBA/2023-07-27-0001193125-23-196159-d532458d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523196159/d532458d8k.htm) |
| WBA | 窗内 | 8-K | 2023-08-10 | 2023-08-09 | 1.01,2.03,9.01 | [documents/WBA/2023-08-10-0001193125-23-207773-d542330d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523207773/d542330d8k.htm) |
| WBA | 窗内 | 8-K | 2023-09-01 | 2023-08-31 | 5.02,7.01,9.01 | [documents/WBA/2023-09-01-0001193125-23-226884-d497068d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523226884/d497068d8k.htm) |
| WBA | 窗内 | 8-K/A | 2023-09-22 | 2023-08-31 | 5.02 | [documents/WBA/2023-09-22-0001193125-23-240570-d331934d8ka.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523240570/d331934d8ka.htm) |
| WBA | 窗内 | 8-K | 2023-10-11 | 2023-10-10 | 5.02,7.01,9.01 | [documents/WBA/2023-10-11-0001193125-23-253805-d559360d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523253805/d559360d8k.htm) |
| WBA | 窗内 | 8-K | 2023-10-12 | 2023-10-12 | 2.02,7.01,9.01 | [documents/WBA/2023-10-12-0001193125-23-254615-d558457d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523254615/d558457d8k.htm) |
| WBA | 窗内 | 10-K | 2023-10-12 | 2023-08-31 | — | [documents/WBA/2023-10-12-0001618921-23-000062-wba-20230831.htm](https://www.sec.gov/Archives/edgar/data/1618921/000161892123000062/wba-20230831.htm) |
| WBA | 窗内 | 8-K/A | 2023-10-30 | 2023-07-27 | 5.02,9.01 | [documents/WBA/2023-10-30-0001193125-23-265359-d535453d8ka.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523265359/d535453d8ka.htm) |
| WBA | 窗内 | 8-K | 2023-11-24 | 2023-11-24 | 7.01,9.01 | [documents/WBA/2023-11-24-0001193125-23-282616-d545705d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312523282616/d545705d8k.htm) |
| WBA | 窗内 | 8-K | 2024-01-04 | 2024-01-04 | 2.02,7.01,9.01 | [documents/WBA/2024-01-04-0001193125-24-001901-d605513d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312524001901/d605513d8k.htm) |
| WBA | 窗内 | 10-Q | 2024-01-04 | 2023-11-30 | — | [documents/WBA/2024-01-04-0001618921-24-000004-wba-20231130.htm](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000004/wba-20231130.htm) |
| WBA | 窗内 | 8-K | 2024-01-31 | 2024-01-25 | 5.07 | [documents/WBA/2024-01-31-0001193125-24-021052-d701412d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312524021052/d701412d8k.htm) |
| WBA | 窗内 | 8-K | 2024-02-08 | 2024-02-06 | 5.02,7.01,9.01 | [documents/WBA/2024-02-08-0001193125-24-028508-d751581d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312524028508/d751581d8k.htm) |
| WBA | 窗内 | 8-K | 2024-03-28 | 2024-03-28 | 2.02,7.01,9.01 | [documents/WBA/2024-03-28-0001193125-24-079608-d817592d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312524079608/d817592d8k.htm) |
| WBA | 窗内 | 8-K | 2024-03-28 | 2024-03-27 | 5.02,9.01 | [documents/WBA/2024-03-28-0001193125-24-080799-d797051d8k.htm](https://www.sec.gov/Archives/edgar/data/1618921/000119312524080799/d797051d8k.htm) |
| WBA | 窗内 | 10-Q | 2024-03-28 | 2024-02-29 | — | [documents/WBA/2024-03-28-0001618921-24-000035-wba-20240229.htm](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000035/wba-20240229.htm) |
| WBA | 尾部季度 | 10-Q | 2024-06-27 | 2024-05-31 | — | [documents/WBA/2024-06-27-0001618921-24-000065-wba-20240531.htm](https://www.sec.gov/Archives/edgar/data/1618921/000161892124000065/wba-20240531.htm) |

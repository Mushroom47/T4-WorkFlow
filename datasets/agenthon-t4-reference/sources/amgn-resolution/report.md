# AMGN 日期与公开参考研究范围核查

2026-10-07 的事实核查已完成，随后主办方 [#27 的公开答复（2026-10-07T15:42:04Z）](https://github.com/Agenthon-2026/track4-analysis-public/issues/27#issuecomment-6041356736) 解除 AMGN 日期口径歧义：目标是 June-2023 单季度 GAAP diluted EPS；resolution_date 仅说明 horizon，expected_report_date 为实体表列，scorer 不读取两者。8 月 3 日实际报告晚于题面 8 月 2 日不会丢弃或改变该实体的处理。AMGN 的本地状态现在为 `fact_status=verified`、`task_alignment=aligned`、`status=verified`，可默认纳入；`first_publication_status` 与 `official_outcome_status` 继续为 `unconfirmed`，核心值 `2.57/up` 未改变。

原始研究阶段仅新增本目录证据和不含重建结果的草案。此次日期收敛仅更新 AMGN 派生说明、质量覆盖记录、相关审计限制与回归；原冻结 task 字节和日期不改写。完整 GitHub 评论未落盘，`official-clarification-20261007.json` 只保存原创摘要、来源 URL、作者、实际取回日期和内存计算的上游 body/API SHA；这些上游 SHA 不能当作本地可回读全文哈希。

首次研究取回时的官方 T4 HEAD 为 `1c744e1d6725340643a533f436517d72b53ca0e1`，当时公开 task/card 与冻结副本逐字节相同；task cutoff 为 `2023-07-14`、resolution 为 `2023-08-02`，AMGN expected report 为 `2023-08-01`。该轮曾读取全部公开 issue 正文及 #3/#23/#24/#25/#26 评论，#26 当时零评论。后续 #27 明确这些结果日期填写早于真实公告，但不构成目标截止；主办方讨论修正日期，若公开资源变更会在 issue 说明。本次不声称日期修正版已经发布，也没有重新抓取冻结输入。

| 事实 | 独立原件核验 | 可以支持的范围 |
|---|---|---|
| 7 月 31 日预告 | 保存 issuer 原始 HTML，正文安排 8 月 3 日收市后报告 | 预告网页本身早于 resolution；预告的报告日晚于 resolution，二者不能混用 |
| 8 月 3 日实际公告 | 发行人原始公告 URL 和正文日期，GAAP EPS 项目 | 当前保存的日期化原始公告支持实际披露日期和季度数值；不是 2023 年 HTTP 字节快照 |
| June-2023 单季度 EPS | SEC `EarningsPerShareDiluted`，`USD/shares`，`start=2023-04-01`、`end=2023-06-30`，最早已存季度 10-Q observation：`accn=0000318154-23-000053`、`filed=2023-08-04`、`val=2.57` | GAAP diluted 的 90 天季度，不取 basic、non-GAAP 或半年值 |
| June-2022 单季度 EPS | 同一原始 API；`start=2022-04-01`、`end=2022-06-30`，`accn=0000318154-22-000041`、`filed=2022-08-05`、`val=2.45` | 与公开 task 的 prior baseline 一致；后来同比观察值仍为同一数值 |
| 比较方向 | Decimal 对原始季度观察值独立比较：`2.57 > 2.45`，差额 `0.12 USD/share` | 历史事实方向为 `up`；没有比较组织者私有 outcome |

SEC 2023 年 10-Q 正文也通过 web 读取，损益表的 three-month 列 diluted EPS 为上述两值；six-month 列是 `7.86/5.13`，不能代替季度。该正文直接 HTTP 下载为 403，因此没有保存伪造 HTML 或原件哈希。[SEC 2023Q2 原始申报](https://www.sec.gov/Archives/edgar/data/318154/000031815423000053/amgn-20230630.htm)。完整单指标 API 的保存原件 SHA 与既有 metadata 回读一致；其原取回时间 `2026-10-07T08:14:25.557018+00:00` 与本轮复制时间分别保存。

完整 prompt 和 `label_assertions` 指向 June-2023 季度，要求 reported AFTER cutoff。[#23（2026-10-04）](https://github.com/Agenthon-2026/track4-analysis-public/issues/23#issuecomment-5985154828) 与 [#25（2026-10-07）](https://github.com/Agenthon-2026/track4-analysis-public/issues/25#issuecomment-6029255707) 分别说明语义来源及 diluted EPS 数量。随后 [#27](https://github.com/Agenthon-2026/track4-analysis-public/issues/27#issuecomment-6041356736) 明确 point 和 interval 均针对同一单季度 GAAP diluted EPS，来源为 SEC XBRL `EarningsPerShareDiluted`。`cutoff_date` 约束提交推理引用的段落时间，结果参考来源可以在 cutoff 之后发布，不能误将 `reference.sources` 当作预测时可引用输入。

日期收敛的具体做法是保留 `actual_release_date=2023-08-03`、预告日期 `2023-07-31` 和 `release_after_resolution=true`，将 `official_task_date_contract_status` 更新为 `aligned_by_public_clarification`。旧 `awaiting_organizer_clarification` 记录与原核查时间保存在 `historical_date_contract_check`，不覆盖历史事实。审计直接回读已隔离的发行人原件 dateline 来检查公告与预告角色；负控将实际公告日期伪改为 7 月 31 日，必须失败。日期解释解除暂定限制，并没有把未知首发版本或私有 outcome 改成确认。

关于公开发布，需要分清四个范围。[#24 的 2026-10-05 答复](https://github.com/Agenthon-2026/track4-analysis-public/issues/24#issuecomment-6001199755) 允许使用公开 practice 的首次发布值设置 constants/design choices；[2026-10-07 补充](https://github.com/Agenthon-2026/track4-analysis-public/issues/24#issuecomment-6029140058) 将它明确适用于 every Final task，且保留 source、retrieval date、`ARTIFACT_PROVENANCE.md` 和 practice in-sample disclosure 条件。这个使用例外没有取消 task-answer lookup、外部推理 corpus 或第三方版权限制，也没有直接回答参考研究数据的发布问题。

[比赛规则 §7](https://www.agenthon.net/rules/) 要求留意团队保密和引用的权利，不能把本地参考文件宣称为官方答案。[Licensing Policy §8](https://www.agenthon.net/licensing/) 允许参与者独立发布自身作品；§3 仍按具体输入许可处理。按统一发布方案，原创计算代码、方法、派生事实、来源定位和哈希可以发布；额外 SEC/IR 原件与许可不明全文留在本地隔离缓存。此次 #27 只解释 AMGN 目标和日期字段，没有额外授权固定答案回放或 lookup，也未确认任何私有结果。

本 unit 的逐文件 manifest 明确 task/card 为 `CC-BY-4.0`、redistributable；保存和公开时应保留归属及许可。SEC corpus 的逐文件条款是 public record、可按原申报再分发，但申报者/SEC 没有额外版权授权；不要因顶层 MIT 或旧 THIRD-PARTY-NOTICES 的概括将发行人全文改标 public domain。SEC 网站的 Website Dissemination 说明其网站 public information 可复制分发，并建议引用 SEC 来源；这不等于发行人原始版权消失。[SEC 网站说明](https://www.sec.gov/about/privacy-information)。

本轮取得 [Amgen Terms of Use](https://www.amgen.com/terms-of-use) 原件，Effective Date 为 2024-02-20，§3 对自身使用、公开/商业使用、AI/自动采集设定限制。因此此前保存的 issuer 两份完整 HTML 和本目录的 issuer 原件应排除在公开包之外，不能根据“公开可读”推定可随库全文分发。为公开复现，优先提供自己的计算代码、季度选择规则、来源 URL/哈希及依法获取的 SEC 结构化输入；按根任务的统一发布方案，将公司申报/IR 原始材料置于本地缓存，并说明合法获取路径。研究者的事实判断与第三方文档表达是不同资产。

`amgn-resolution-check.json` 保存季度选择、事实检查、历史待确认判断和后续日期澄清；`official-clarification-20261007.json` 保存此次原创官方解释摘要。`evidence-manifest.json` 的原始来源下载、失败、31 份字节核查均属于原研究时点的记录，新增摘要另以 `derived_report_hashes` 记录自己的可回读字节；研究记录不能计作独立公式复算。3 次旧 SEC HTTP 失败保留错误，没有伪造原件。公开包移出的完整正文按 `public-source-catalog.json` 在本地缓存补齐，浏览摘要不当作 HTTP 原件。

完整上游Markdown原文的孤立副本以 `.md.txt` 保存，字节/hash保持不变；其中相对链接属于上游仓库上下文。请按source-register的原始官方URL阅读，不能假设上游相对文件在本目录存在。

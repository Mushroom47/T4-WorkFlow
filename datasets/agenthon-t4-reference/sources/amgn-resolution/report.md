# AMGN 日期与公开参考研究范围核查

核查日期为 2026-10-07。结论是：AMGN 的 June-2023 单季度 GAAP diluted EPS 和同比方向能够由公开原始来源独立验收；当前公开题面日期没有修订，而 resolution 对随后实际披露的季度结果有无硬截止作用，仍需主办方说明。公开代码和参与者自写方法不因参赛而自动要求保密，但 #24 没有明确给出公开发布重建参考值的专门许可；第三方正文必须按实际权利另行处理。

本目录仅新增研究证据和草案，没有修改 reference、research、QA、tools、开发文档、Git 或 Linear，也没有发送任何外部消息。`official-questions-draft.md` 不包含重建数值或方向标签。

当前官方 T4 远端 HEAD 仍为 `1c744e1d6725340643a533f436517d72b53ca0e1`。本轮取回的公开 task/card 与冻结副本逐字节相同；task 的 cutoff 是 `2023-07-14`、resolution 是 `2023-08-02`，AMGN expected report 是 `2023-08-01`。本轮保存了全部公开 issue 正文及 #3/#23/#24/#25/#26 的完整评论；相关评论没有新解释 AMGN 日期，#26 在取回时仍为零评论。没有声称检查了所有历史 issue 的全部评论。

| 事实 | 独立原件核验 | 可以支持的范围 |
|---|---|---|
| 7 月 31 日预告 | 保存 issuer 原始 HTML，正文安排 8 月 3 日收市后报告 | 预告网页本身早于 resolution；预告的报告日晚于 resolution，二者不能混用 |
| 8 月 3 日实际公告 | 发行人原始公告 URL 和正文日期，GAAP EPS 项目 | 当前保存的日期化原始公告支持实际披露日期和季度数值；不是 2023 年 HTTP 字节快照 |
| June-2023 单季度 EPS | SEC `EarningsPerShareDiluted`，`USD/shares`，`start=2023-04-01`、`end=2023-06-30`，最早已存季度 10-Q observation：`accn=0000318154-23-000053`、`filed=2023-08-04`、`val=2.57` | GAAP diluted 的 90 天季度，不取 basic、non-GAAP 或半年值 |
| June-2022 单季度 EPS | 同一原始 API；`start=2022-04-01`、`end=2022-06-30`，`accn=0000318154-22-000041`、`filed=2022-08-05`、`val=2.45` | 与公开 task 的 prior baseline 一致；后来同比观察值仍为同一数值 |
| 比较方向 | Decimal 对原始季度观察值独立比较：`2.57 > 2.45`，差额 `0.12 USD/share` | 历史事实方向为 `up`；没有比较组织者私有 outcome |

SEC 2023 年 10-Q 正文也通过 web 读取，损益表的 three-month 列 diluted EPS 为上述两值；six-month 列是 `7.86/5.13`，不能代替季度。该正文直接 HTTP 下载为 403，因此没有保存伪造 HTML 或原件哈希。[SEC 2023Q2 原始申报](https://www.sec.gov/Archives/edgar/data/318154/000031815423000053/amgn-20230630.htm)。完整单指标 API 的保存原件 SHA 与既有 metadata 回读一致；其原取回时间 `2026-10-07T08:14:25.557018+00:00` 与本轮复制时间分别保存。

完整 prompt 和 `label_assertions` 明确指向 June-2023 季度，要求 reported AFTER cutoff，没有明确要求 before resolution。主办方 [#23，2026-10-04](https://github.com/Agenthon-2026/track4-analysis-public/issues/23#issuecomment-5985154828) 指定从 prompt、target、label assertions、entity table 判断数量语义；[#25，2026-10-07](https://github.com/Agenthon-2026/track4-analysis-public/issues/25#issuecomment-6029255707) 确认本题 numeric target 为 diluted EPS。这些文字支持季度数量定义，但不能替主办方决定 resolution 是否为硬截止，也没有修订该字段。

可事实验收的解决方式是把两种结论分开：上述数值、季度和方向标为已核实历史事实；单列 `actual_release_date=2023-08-03`、`release_after_resolution=true`、`official_task_date_contract_status=awaiting_organizer_clarification`。若整行 status 的约定包含题面日期合同已经无歧义，则仍保留 provisional；不能仅凭数值一致把未知合同改成已确认。若主办方确认 prompt 指定季度的实际首发值有效，可解除该日期暂定项并保存具体公开回复；若主办方修订 resolution，保留原冻结输入和新版本，不能静默改写历史 task 指纹；若日期为硬截止，按公开规则单列该实体的不可用/例外状态，不自行制造截止日 EPS 或标签。精确问题草案已保存，未请求隐藏答案。

关于公开发布，需要分清四个范围。[#24 的 2026-10-05 答复](https://github.com/Agenthon-2026/track4-analysis-public/issues/24#issuecomment-6001199755) 允许使用公开 practice 的首次发布值设置 constants/design choices；[2026-10-07 补充](https://github.com/Agenthon-2026/track4-analysis-public/issues/24#issuecomment-6029140058) 将它明确适用于 every Final task，且保留 source、retrieval date、`ARTIFACT_PROVENANCE.md` 和 practice in-sample disclosure 条件。这个使用例外没有取消 task-answer lookup、外部推理 corpus 或第三方版权限制，也没有直接回答参考研究数据的发布问题。

[比赛规则 §7](https://www.agenthon.net/rules/) 禁止获取、重建或公开非公开测试材料。本轮取数来自独立公共来源，未从平台或私有 outcome 提取，不能将这份参考文件宣称为官方答案。[Licensing Policy §8](https://www.agenthon.net/licensing/) 明确参与者可以独立发布自身作品；§3 按公开资源的具体许可处理。这支持自写代码和方法的自主公开，不构成对整个参考数据包的统一第三方再许可。当前已读文字未明确禁止发布独立研究的公共历史事实值，但这是对规则范围的解释，不是主办方已经回答该问题；草案单列询问是否存在比赛特有的额外限制。

本 unit 的逐文件 manifest 明确 task/card 为 `CC-BY-4.0`、redistributable；保存和公开时应保留归属及许可。SEC corpus 的逐文件条款是 public record、可按原申报再分发，但申报者/SEC 没有额外版权授权；不要因顶层 MIT 或旧 THIRD-PARTY-NOTICES 的概括将发行人全文改标 public domain。SEC 网站的 Website Dissemination 说明其网站 public information 可复制分发，并建议引用 SEC 来源；这不等于发行人原始版权消失。[SEC 网站说明](https://www.sec.gov/about/privacy-information)。

本轮取得 [Amgen Terms of Use](https://www.amgen.com/terms-of-use) 原件，Effective Date 为 2024-02-20，§3 对自身使用、公开/商业使用、AI/自动采集设定限制。因此此前保存的 issuer 两份完整 HTML 和本目录的 issuer 原件应排除在公开包之外，不能根据“公开可读”推定可随库全文分发。为公开复现，优先提供自己的计算代码、季度选择规则、来源 URL/哈希及依法获取的 SEC 结构化输入；按根任务的统一发布方案，将公司申报/IR 原始材料置于本地缓存，并说明合法获取路径。研究者的事实判断与第三方文档表达是不同资产。

`amgn-resolution-check.json` 保存季度选择、逐项事实检查和边界；`evidence-manifest.json` 保存本轮来源及失败。31 份保存/复制原件均实际回读 SHA 与 bytes，通过；3 次新 HTTP 失败（SEC 网站说明、SEC 10-Q 正文、SEC submissions）均保存错误且没有伪造原件。浏览工具对部分 URL 的失败另保存在 `web-checks.json`，不把浏览摘要作为 HTTP 原件。主要来源已收敛，不继续重复查询。

完整上游Markdown原文的孤立副本以 `.md.txt` 保存，字节/hash保持不变；其中相对链接属于上游仓库上下文。请按source-register的原始官方URL阅读，不能假设上游相对文件在本目录存在。
